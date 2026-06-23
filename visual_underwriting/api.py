import json
from uuid import uuid4

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from visual_underwriting.agent import VisualUnderwritingAgent
from visual_underwriting.config import Settings, get_settings
from visual_underwriting.image_validation import ImageValidationError, validate_image_upload
from visual_underwriting.logging import configure_logging
from visual_underwriting.schemas import (
    AssessmentMetadata,
    AssetType,
    Decision,
    UnderwritingMetadata,
    UnderwritingResponse,
    VisualAssessmentResponse,
)
from visual_underwriting.storage import build_image_hash_store
from visual_underwriting.ui import render_underwriting_ui
from visual_underwriting.vision import AnthropicVisionClient, VisionModelError, VisualAssessmentClient


def create_app(
    settings: Settings | None = None,
    agent: VisualUnderwritingAgent | None = None,
    assessment_client: VisualAssessmentClient | None = None,
) -> FastAPI:
    configure_logging()
    resolved_settings = settings or get_settings()
    vision_client = AnthropicVisionClient(resolved_settings)
    resolved_agent = agent or VisualUnderwritingAgent(
        vision_client=vision_client,
        image_hash_store=build_image_hash_store(resolved_settings),
        settings=resolved_settings,
    )
    resolved_assessment_client = assessment_client or vision_client

    app = FastAPI(title="Visual Underwriting Service", version="0.1.0")
    app.state.settings = resolved_settings
    app.state.visual_underwriting_agent = resolved_agent
    app.state.visual_assessment_client = resolved_assessment_client

    @app.get("/", response_class=HTMLResponse)
    @app.get("/ui", response_class=HTMLResponse)
    async def underwriting_ui() -> HTMLResponse:
        return HTMLResponse(render_underwriting_ui())

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/underwriting/assess", response_model=VisualAssessmentResponse)
    async def assess_image(
        image: UploadFile = File(...),
        metadata: str = Form(default="{}"),
        x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    ) -> VisualAssessmentResponse:
        request_id = x_request_id or str(uuid4())
        parsed_metadata = _parse_assessment_metadata(metadata)
        content = await image.read(app.state.settings.max_image_bytes + 1)

        try:
            validated_image = validate_image_upload(content, app.state.settings.max_image_bytes)
        except ImageValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        assessment_client: VisualAssessmentClient = app.state.visual_assessment_client
        try:
            result = await run_in_threadpool(
                assessment_client.assess_image,
                image_bytes=validated_image.content,
                mime_type=validated_image.mime_type,
                metadata=parsed_metadata,
                request_id=request_id,
            )
        except VisionModelError as exc:
            return VisualAssessmentResponse(
                request_id=request_id,
                decision=Decision.REFER_TO_MANUAL_REVIEW,
                explanation=[
                    "Vision assessment failed after retries; route this submission to manual review.",
                    str(exc),
                ],
            )

        return VisualAssessmentResponse(
            request_id=request_id,
            decision=Decision.SCORED,
            result=result,
            explanation=result.explanation,
        )

    @app.post("/v1/underwriting/shop", response_model=UnderwritingResponse)
    async def score_shop(
        image: UploadFile = File(...),
        metadata: str = Form(...),
        x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    ) -> UnderwritingResponse:
        return await _score_submission(
            app=app,
            asset_type=AssetType.SHOP,
            image=image,
            metadata_json=metadata,
            request_id=x_request_id or str(uuid4()),
        )

    @app.post("/v1/underwriting/cattle", response_model=UnderwritingResponse)
    async def score_cattle(
        image: UploadFile = File(...),
        metadata: str = Form(...),
        x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
    ) -> UnderwritingResponse:
        parsed_metadata = _parse_metadata(metadata)
        if parsed_metadata.declared_cattle_count is None:
            raise HTTPException(status_code=422, detail="declared_cattle_count is required for cattle submissions")

        return await _score_submission(
            app=app,
            asset_type=AssetType.CATTLE,
            image=image,
            parsed_metadata=parsed_metadata,
            request_id=x_request_id or str(uuid4()),
        )

    return app


async def _score_submission(
    *,
    app: FastAPI,
    asset_type: AssetType,
    image: UploadFile,
    request_id: str,
    metadata_json: str | None = None,
    parsed_metadata: UnderwritingMetadata | None = None,
) -> UnderwritingResponse:
    metadata = parsed_metadata or _parse_metadata(metadata_json or "")
    content = await image.read(app.state.settings.max_image_bytes + 1)

    try:
        validated_image = validate_image_upload(content, app.state.settings.max_image_bytes)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    agent: VisualUnderwritingAgent = app.state.visual_underwriting_agent
    return await run_in_threadpool(
        agent.score,
        asset_type=asset_type,
        image=validated_image,
        metadata=metadata,
        request_id=request_id,
    )


def _parse_metadata(metadata_json: str) -> UnderwritingMetadata:
    try:
        payload = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="metadata must be valid JSON") from exc

    try:
        return UnderwritingMetadata.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=jsonable_encoder(exc.errors())) from exc


def _parse_assessment_metadata(metadata_json: str) -> AssessmentMetadata:
    try:
        payload = json.loads(metadata_json or "{}")
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="metadata must be valid JSON") from exc

    try:
        return AssessmentMetadata.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=jsonable_encoder(exc.errors())) from exc
