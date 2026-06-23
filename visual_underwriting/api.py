import json
from uuid import uuid4

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from visual_underwriting.agent import VisualUnderwritingAgent
from visual_underwriting.config import Settings, get_settings
from visual_underwriting.image_validation import ImageValidationError, validate_image_upload
from visual_underwriting.logging import configure_logging
from visual_underwriting.schemas import AssetType, UnderwritingMetadata, UnderwritingResponse
from visual_underwriting.storage import build_image_hash_store
from visual_underwriting.vision import AnthropicVisionClient


def create_app(settings: Settings | None = None, agent: VisualUnderwritingAgent | None = None) -> FastAPI:
    configure_logging()
    resolved_settings = settings or get_settings()
    resolved_agent = agent or VisualUnderwritingAgent(
        vision_client=AnthropicVisionClient(resolved_settings),
        image_hash_store=build_image_hash_store(resolved_settings),
        settings=resolved_settings,
    )

    app = FastAPI(title="Visual Underwriting Service", version="0.1.0")
    app.state.settings = resolved_settings
    app.state.visual_underwriting_agent = resolved_agent

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

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
