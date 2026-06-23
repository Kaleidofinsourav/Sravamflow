import base64
import json
import logging
from typing import Any, Protocol

from pydantic import ValidationError

from visual_underwriting.config import Settings
from visual_underwriting.prompts import load_prompt_template, render_prompt_template
from visual_underwriting.schemas import (
    AssessmentMetadata,
    AssetType,
    UnderwritingMetadata,
    VisionUnderwritingResult,
    VisualAssessmentResult,
    visual_assessment_json_schema_for_prompt,
    vision_json_schema_for_prompt,
)

logger = logging.getLogger(__name__)


class VisionModelError(RuntimeError):
    pass


class VisionClient(Protocol):
    def score_image(
        self,
        *,
        asset_type: AssetType,
        image_bytes: bytes,
        mime_type: str,
        metadata: UnderwritingMetadata,
        request_id: str,
    ) -> VisionUnderwritingResult:
        ...


class VisualAssessmentClient(Protocol):
    def assess_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        metadata: AssessmentMetadata,
        request_id: str,
    ) -> VisualAssessmentResult:
        ...


class AnthropicVisionClient:
    def __init__(self, settings: Settings, anthropic_client: Any | None = None) -> None:
        self._settings = settings
        self._client = anthropic_client or self._build_anthropic_client(settings)
        self._underwriting_prompt_template = load_prompt_template(settings.underwriting_prompt_path)
        self._assessment_prompt_template = load_prompt_template(settings.assessment_prompt_path)

    def score_image(
        self,
        *,
        asset_type: AssetType,
        image_bytes: bytes,
        mime_type: str,
        metadata: UnderwritingMetadata,
        request_id: str,
    ) -> VisionUnderwritingResult:
        last_error: Exception | None = None
        attempts = self._settings.anthropic_max_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                response = self._client.messages.create(
                    model=self._settings.anthropic_model,
                    max_tokens=1200,
                    temperature=0,
                    system=(
                        "You are a visual credit-underwriting assistant. Return only JSON that "
                        "matches the provided schema. Do not include markdown or commentary."
                    ),
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": base64.b64encode(image_bytes).decode("ascii"),
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": self._build_prompt(asset_type=asset_type, metadata=metadata),
                                },
                            ],
                        }
                    ],
                )
                return self._parse_response(response)
            except Exception as exc:  # noqa: BLE001 - any SDK/parsing failure routes to retry/manual review.
                last_error = exc
                logger.warning(
                    "vision_model_attempt_failed",
                    extra={
                        "request_id": request_id,
                        "attempt": attempt,
                        "max_attempts": attempts,
                        "error": str(exc),
                    },
                )

        raise VisionModelError("vision model failed after retries") from last_error

    def assess_image(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        metadata: AssessmentMetadata,
        request_id: str,
    ) -> VisualAssessmentResult:
        last_error: Exception | None = None
        attempts = self._settings.anthropic_max_retries + 1

        for attempt in range(1, attempts + 1):
            try:
                response = self._client.messages.create(
                    model=self._settings.anthropic_model,
                    max_tokens=1400,
                    temperature=0,
                    system=(
                        "You are a guarded visual business-assessment assistant. Return only JSON "
                        "that matches the provided schema. Do not include markdown or commentary. "
                        "Use only visible evidence in the image and optional metadata. Do not infer "
                        "income, caste, religion, gender, age, or other protected/sensitive traits. "
                        "If evidence is unclear, lower confidence and explain the uncertainty."
                    ),
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": base64.b64encode(image_bytes).decode("ascii"),
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": self._build_assessment_prompt(metadata=metadata),
                                },
                            ],
                        }
                    ],
                )
                return self._parse_assessment_response(response)
            except Exception as exc:  # noqa: BLE001 - SDK/parsing failures route to retry/manual review.
                last_error = exc
                logger.warning(
                    "vision_assessment_attempt_failed",
                    extra={
                        "request_id": request_id,
                        "attempt": attempt,
                        "max_attempts": attempts,
                        "error": str(exc),
                    },
                )

        raise VisionModelError("vision assessment failed after retries") from last_error

    @staticmethod
    def _build_anthropic_client(settings: Settings) -> Any:
        import anthropic

        kwargs: dict[str, Any] = {"timeout": settings.anthropic_timeout_seconds}
        if settings.anthropic_api_key:
            kwargs["api_key"] = settings.anthropic_api_key
        return anthropic.Anthropic(**kwargs)

    def _build_prompt(self, *, asset_type: AssetType, metadata: UnderwritingMetadata) -> str:
        return render_prompt_template(
            self._underwriting_prompt_template,
            {
                "asset_type": asset_type.value,
                "metadata_json": metadata.model_dump_json(),
                "schema_json": json.dumps(vision_json_schema_for_prompt(), separators=(",", ":")),
            },
        )

    @classmethod
    def _parse_response(cls, response: Any) -> VisionUnderwritingResult:
        text = cls._extract_text(response)
        raw_json = cls._extract_json_object(text)
        try:
            payload = json.loads(raw_json)
            return VisionUnderwritingResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise VisionModelError("vision model returned malformed underwriting JSON") from exc

    def _build_assessment_prompt(self, *, metadata: AssessmentMetadata) -> str:
        return render_prompt_template(
            self._assessment_prompt_template,
            {
                "metadata_json": metadata.model_dump_json(exclude_none=True),
                "schema_json": json.dumps(visual_assessment_json_schema_for_prompt(), separators=(",", ":")),
            },
        )

    @classmethod
    def _parse_assessment_response(cls, response: Any) -> VisualAssessmentResult:
        text = cls._extract_text(response)
        raw_json = cls._extract_json_object(text)
        try:
            payload = json.loads(raw_json)
            return VisualAssessmentResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise VisionModelError("vision model returned malformed assessment JSON") from exc

    @staticmethod
    def _extract_text(response: Any) -> str:
        content = getattr(response, "content", None)
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            chunks: list[str] = []
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    chunks.append(block["text"])
                    continue
                block_text = getattr(block, "text", None)
                if isinstance(block_text, str):
                    chunks.append(block_text)
            if chunks:
                return "\n".join(chunks)

        raise VisionModelError("vision model response did not contain text")

    @staticmethod
    def _extract_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise VisionModelError("vision model response did not contain a JSON object")
        return text[start : end + 1]
