import logging
import math
from datetime import time

from visual_underwriting.config import Settings
from visual_underwriting.schemas import (
    AssetType,
    Decision,
    FraudFlag,
    FraudSeverity,
    ImageValidationResult,
    UnderwritingMetadata,
    UnderwritingResponse,
    VisionScoreComponents,
    VisionUnderwritingResult,
)
from visual_underwriting.storage import ImageHashStore
from visual_underwriting.vision import VisionClient, VisionModelError

logger = logging.getLogger(__name__)


SCORING_WEIGHTS = {
    "asset_presence": 0.30,
    "asset_quality": 0.30,
    "context_consistency": 0.20,
    "repayment_capacity_signal": 0.20,
}


class VisualUnderwritingAgent:
    def __init__(
        self,
        *,
        vision_client: VisionClient,
        image_hash_store: ImageHashStore,
        settings: Settings,
    ) -> None:
        self._vision_client = vision_client
        self._image_hash_store = image_hash_store
        self._settings = settings

    def score(
        self,
        *,
        asset_type: AssetType,
        image: ImageValidationResult,
        metadata: UnderwritingMetadata,
        request_id: str,
    ) -> UnderwritingResponse:
        fraud_flags = self._run_integrity_checks(image=image, metadata=metadata)

        try:
            model_result = self._vision_client.score_image(
                asset_type=asset_type,
                image_bytes=image.content,
                mime_type=image.mime_type,
                metadata=metadata,
                request_id=request_id,
            )
        except VisionModelError as exc:
            response = UnderwritingResponse(
                request_id=request_id,
                asset_type=asset_type,
                decision=Decision.REFER_TO_MANUAL_REVIEW,
                fraud_flags=fraud_flags,
                explanation=[
                    "Vision model failed after retries; routed to manual underwriting review.",
                    str(exc),
                ],
            )
            self._log_outcome(response)
            return response

        fraud_flags.extend(model_result.fraud_flags)

        if model_result.confidence < self._settings.low_confidence_threshold:
            fraud_flags.append(
                FraudFlag(
                    code="LOW_VISION_CONFIDENCE",
                    severity=FraudSeverity.SOFT,
                    message=(
                        "Vision model confidence "
                        f"{model_result.confidence:.2f} is below configured threshold "
                        f"{self._settings.low_confidence_threshold:.2f}."
                    ),
                )
            )

        if asset_type == AssetType.CATTLE and metadata.declared_cattle_count is not None:
            self._append_cattle_count_flag(
                fraud_flags=fraud_flags,
                declared_count=metadata.declared_cattle_count,
                observed_count=model_result.observed_cattle_count,
            )

        decision = (
            Decision.REFER_TO_MANUAL_REVIEW
            if self._requires_manual_review(fraud_flags=fraud_flags, model_result=model_result)
            else Decision.SCORED
        )

        response = UnderwritingResponse(
            request_id=request_id,
            asset_type=asset_type,
            decision=decision,
            weighted_score=self.calculate_weighted_score(model_result.score_components),
            confidence=model_result.confidence,
            fraud_flags=fraud_flags,
            explanation=model_result.explanation,
            model_result=model_result,
        )
        self._log_outcome(response)
        return response

    def _run_integrity_checks(self, *, image: ImageValidationResult, metadata: UnderwritingMetadata) -> list[FraudFlag]:
        fraud_flags: list[FraudFlag] = []

        if not self._image_hash_store.record_if_new(image.sha256):
            fraud_flags.append(
                FraudFlag(
                    code="DUPLICATE_IMAGE",
                    severity=FraudSeverity.HARD,
                    message="This exact image hash was already submitted.",
                )
            )

        distance_meters = haversine_meters(
            metadata.captured_lat,
            metadata.captured_lng,
            metadata.declared_lat,
            metadata.declared_lng,
        )
        if distance_meters > self._settings.geofence_radius_meters:
            fraud_flags.append(
                FraudFlag(
                    code="GPS_OUT_OF_GEOFENCE",
                    severity=FraudSeverity.HARD,
                    message=(
                        f"Captured GPS is {distance_meters:.0f}m from declared location, "
                        f"outside {self._settings.geofence_radius_meters:.0f}m limit."
                    ),
                )
            )

        if not captured_within_declared_business_hours(metadata):
            fraud_flags.append(
                FraudFlag(
                    code="OUTSIDE_DECLARED_BUSINESS_HOURS",
                    severity=FraudSeverity.SOFT,
                    message="Image timestamp is outside declared business hours.",
                )
            )

        return fraud_flags

    @staticmethod
    def calculate_weighted_score(score_components: VisionScoreComponents) -> float:
        raw_score = sum(
            getattr(score_components, component_name) * weight
            for component_name, weight in SCORING_WEIGHTS.items()
        )
        return round(raw_score, 2)

    @staticmethod
    def _append_cattle_count_flag(
        *,
        fraud_flags: list[FraudFlag],
        declared_count: int,
        observed_count: int | None,
    ) -> None:
        if observed_count is None:
            fraud_flags.append(
                FraudFlag(
                    code="CATTLE_COUNT_NOT_OBSERVED",
                    severity=FraudSeverity.SOFT,
                    message="Vision model could not determine the cattle count.",
                )
            )
            return

        if observed_count != declared_count:
            fraud_flags.append(
                FraudFlag(
                    code="CATTLE_COUNT_MISMATCH",
                    severity=FraudSeverity.SOFT,
                    message=f"Declared cattle count {declared_count} differs from observed count {observed_count}.",
                )
            )

    def _requires_manual_review(
        self,
        *,
        fraud_flags: list[FraudFlag],
        model_result: VisionUnderwritingResult,
    ) -> bool:
        if any(flag.severity == FraudSeverity.HARD for flag in fraud_flags):
            return True
        return model_result.confidence < self._settings.low_confidence_threshold

    @staticmethod
    def _log_outcome(response: UnderwritingResponse) -> None:
        for flag in response.fraud_flags:
            logger.info(
                "visual_underwriting_fraud_flag",
                extra={
                    "request_id": response.request_id,
                    "asset_type": response.asset_type.value,
                    "fraud_flag_code": flag.code,
                    "fraud_flag_severity": flag.severity.value,
                    "fraud_flag_message": flag.message,
                },
            )

        logger.info(
            "visual_underwriting_decision",
            extra={
                "request_id": response.request_id,
                "asset_type": response.asset_type.value,
                "decision": response.decision.value,
                "weighted_score": response.weighted_score,
                "confidence": response.confidence,
            },
        )


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_meters = 6_371_000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_meters * c


def captured_within_declared_business_hours(metadata: UnderwritingMetadata) -> bool:
    start_time, end_time = parse_business_hours(metadata.declared_business_hours)
    captured_time = metadata.captured_at.timetz().replace(tzinfo=None)

    if start_time <= end_time:
        return start_time <= captured_time <= end_time
    return captured_time >= start_time or captured_time <= end_time


def parse_business_hours(value: str) -> tuple[time, time]:
    start, end = value.split("-", 1)
    return _parse_time(start), _parse_time(end)


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))
