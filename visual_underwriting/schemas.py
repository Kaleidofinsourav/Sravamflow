from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetType(StrEnum):
    SHOP = "shop"
    CATTLE = "cattle"


class VisualAssetCategory(StrEnum):
    SHOP = "shop"
    CATTLE = "cattle"
    OTHER = "other"
    UNKNOWN = "unknown"


class Decision(StrEnum):
    SCORED = "SCORED"
    REFER_TO_MANUAL_REVIEW = "REFER_TO_MANUAL_REVIEW"


class FraudSeverity(StrEnum):
    HARD = "HARD"
    SOFT = "SOFT"


class UnderwritingMetadata(BaseModel):
    captured_lat: float = Field(ge=-90, le=90)
    captured_lng: float = Field(ge=-180, le=180)
    declared_lat: float = Field(ge=-90, le=90)
    declared_lng: float = Field(ge=-180, le=180)
    captured_at: datetime
    declared_business_hours: str = Field(min_length=5)
    declared_cattle_count: int | None = Field(default=None, ge=0)

    @field_validator("declared_business_hours")
    @classmethod
    def validate_business_hours(cls, value: str) -> str:
        if "-" not in value:
            raise ValueError("declared_business_hours must use HH:MM-HH:MM format")

        start, end = value.split("-", 1)
        for part in (start, end):
            pieces = part.split(":")
            if len(pieces) != 2:
                raise ValueError("declared_business_hours must use HH:MM-HH:MM format")
            hour, minute = pieces
            if not (hour.isdigit() and minute.isdigit()):
                raise ValueError("declared_business_hours must use HH:MM-HH:MM format")
            if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
                raise ValueError("declared_business_hours must use HH:MM-HH:MM format")

        return value


class FraudFlag(BaseModel):
    code: str
    severity: FraudSeverity
    message: str


class VisionScoreComponents(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_presence: float = Field(ge=0, le=100)
    asset_quality: float = Field(ge=0, le=100)
    context_consistency: float = Field(ge=0, le=100)
    repayment_capacity_signal: float = Field(ge=0, le=100)


class VisionUnderwritingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score_components: VisionScoreComponents
    confidence: float = Field(ge=0, le=1)
    fraud_flags: list[FraudFlag] = Field(default_factory=list)
    observed_cattle_count: int | None = Field(default=None, ge=0)
    explanation: list[str] = Field(default_factory=list)


class UnderwritingResponse(BaseModel):
    request_id: str
    asset_type: AssetType
    decision: Decision
    weighted_score: float | None = Field(default=None, ge=0, le=100)
    confidence: float | None = Field(default=None, ge=0, le=1)
    fraud_flags: list[FraudFlag] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)
    model_result: VisionUnderwritingResult | None = None


class AssessmentMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    captured_lat: float | None = Field(default=None, ge=-90, le=90)
    captured_lng: float | None = Field(default=None, ge=-180, le=180)
    captured_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=500)


class ShopVisualScorecard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inventory_score: float = Field(ge=0, le=100)
    footfall_signal_score: float = Field(ge=0, le=100)
    shop_condition_score: float = Field(ge=0, le=100)
    business_vintage_signal_score: float = Field(ge=0, le=100)
    shop_genuineness_score: float = Field(ge=0, le=100)
    operational_activity_score: float = Field(ge=0, le=100)


class VisualAssessmentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identified_asset_type: VisualAssetCategory
    identified_asset_confidence: float = Field(ge=0, le=1)
    overall_confidence_score: float = Field(ge=0, le=100)
    assessment_confidence: float = Field(ge=0, le=1)
    shop_scorecard: ShopVisualScorecard | None = None
    red_flags: list[str] = Field(default_factory=list)
    guardrail_notes: list[str] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)


class VisualAssessmentResponse(BaseModel):
    request_id: str
    decision: Decision
    result: VisualAssessmentResult | None = None
    explanation: list[str] = Field(default_factory=list)


class VisualAssessmentBulkItem(BaseModel):
    filename: str
    status_code: int
    response: VisualAssessmentResponse | None = None
    error: str | None = None


class VisualAssessmentBulkResponse(BaseModel):
    request_id: str
    total: int
    succeeded: int
    failed: int
    items: list[VisualAssessmentBulkItem]


class ImageValidationResult(BaseModel):
    content: bytes
    sha256: str
    mime_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff"]
    size_bytes: int


def vision_json_schema_for_prompt() -> dict[str, Any]:
    return VisionUnderwritingResult.model_json_schema()


def visual_assessment_json_schema_for_prompt() -> dict[str, Any]:
    return VisualAssessmentResult.model_json_schema()
