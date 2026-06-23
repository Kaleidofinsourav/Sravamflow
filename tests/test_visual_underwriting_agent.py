from types import SimpleNamespace

from visual_underwriting.agent import VisualUnderwritingAgent
from visual_underwriting.config import Settings
from visual_underwriting.image_validation import validate_image_upload
from visual_underwriting.schemas import (
    AssetType,
    Decision,
    UnderwritingMetadata,
    VisionScoreComponents,
    VisionUnderwritingResult,
)
from visual_underwriting.storage import InMemoryImageHashStore
from visual_underwriting.vision import AnthropicVisionClient


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class FakeVisionClient:
    def __init__(self, result: VisionUnderwritingResult) -> None:
        self.result = result

    def score_image(self, **kwargs: object) -> VisionUnderwritingResult:
        return self.result


def settings(**overrides: object) -> Settings:
    defaults = {
        "anthropic_api_key": "test-key",
        "anthropic_max_retries": 0,
        "geofence_radius_meters": 500,
        "low_confidence_threshold": 0.65,
        "max_image_bytes": 1024,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def metadata(**overrides: object) -> UnderwritingMetadata:
    defaults = {
        "captured_lat": 12.9716,
        "captured_lng": 77.5946,
        "declared_lat": 12.9717,
        "declared_lng": 77.5947,
        "captured_at": "2026-06-23T10:00:00Z",
        "declared_business_hours": "09:00-18:00",
        "declared_cattle_count": 3,
    }
    defaults.update(overrides)
    return UnderwritingMetadata.model_validate(defaults)


def vision_result(**overrides: object) -> VisionUnderwritingResult:
    defaults = {
        "score_components": {
            "asset_presence": 80,
            "asset_quality": 70,
            "context_consistency": 75,
            "repayment_capacity_signal": 65,
        },
        "confidence": 0.9,
        "fraud_flags": [],
        "observed_cattle_count": 3,
        "explanation": ["Visual evidence supports automated scoring."],
    }
    defaults.update(overrides)
    return VisionUnderwritingResult.model_validate(defaults)


def make_agent(
    *,
    result: VisionUnderwritingResult | None = None,
    store: InMemoryImageHashStore | None = None,
    configured_settings: Settings | None = None,
) -> VisualUnderwritingAgent:
    return VisualUnderwritingAgent(
        vision_client=FakeVisionClient(result or vision_result()),
        image_hash_store=store or InMemoryImageHashStore(),
        settings=configured_settings or settings(),
    )


def validated_image():
    return validate_image_upload(PNG_BYTES, max_image_bytes=1024)


def test_geo_fence_pass_scores_submission() -> None:
    response = make_agent().score(
        asset_type=AssetType.SHOP,
        image=validated_image(),
        metadata=metadata(),
        request_id="geo-pass",
    )

    assert response.decision == Decision.SCORED
    assert "GPS_OUT_OF_GEOFENCE" not in {flag.code for flag in response.fraud_flags}


def test_geo_fence_fail_routes_to_manual_review() -> None:
    response = make_agent().score(
        asset_type=AssetType.SHOP,
        image=validated_image(),
        metadata=metadata(declared_lat=13.5, declared_lng=78.0),
        request_id="geo-fail",
    )

    assert response.decision == Decision.REFER_TO_MANUAL_REVIEW
    assert "GPS_OUT_OF_GEOFENCE" in {flag.code for flag in response.fraud_flags}


def test_duplicate_image_detection_routes_second_submission_to_manual_review() -> None:
    store = InMemoryImageHashStore()
    agent = make_agent(store=store)

    first = agent.score(
        asset_type=AssetType.SHOP,
        image=validated_image(),
        metadata=metadata(),
        request_id="dup-first",
    )
    second = agent.score(
        asset_type=AssetType.SHOP,
        image=validated_image(),
        metadata=metadata(),
        request_id="dup-second",
    )

    assert first.decision == Decision.SCORED
    assert second.decision == Decision.REFER_TO_MANUAL_REVIEW
    assert "DUPLICATE_IMAGE" in {flag.code for flag in second.fraud_flags}


def test_low_confidence_forces_manual_review() -> None:
    response = make_agent(result=vision_result(confidence=0.2)).score(
        asset_type=AssetType.SHOP,
        image=validated_image(),
        metadata=metadata(),
        request_id="low-confidence",
    )

    assert response.decision == Decision.REFER_TO_MANUAL_REVIEW
    assert "LOW_VISION_CONFIDENCE" in {flag.code for flag in response.fraud_flags}


def test_malformed_model_output_is_handled_gracefully() -> None:
    class FakeMessages:
        def create(self, **kwargs: object) -> object:
            return SimpleNamespace(content=[{"text": "not valid underwriting json"}])

    class FakeAnthropic:
        messages = FakeMessages()

    configured_settings = settings()
    agent = VisualUnderwritingAgent(
        vision_client=AnthropicVisionClient(configured_settings, anthropic_client=FakeAnthropic()),
        image_hash_store=InMemoryImageHashStore(),
        settings=configured_settings,
    )

    response = agent.score(
        asset_type=AssetType.SHOP,
        image=validated_image(),
        metadata=metadata(),
        request_id="malformed",
    )

    assert response.decision == Decision.REFER_TO_MANUAL_REVIEW
    assert response.weighted_score is None
    assert response.model_result is None


def test_weighted_score_calculation_correctness() -> None:
    score = VisualUnderwritingAgent.calculate_weighted_score(
        VisionScoreComponents(
            asset_presence=100,
            asset_quality=80,
            context_consistency=60,
            repayment_capacity_signal=50,
        )
    )

    assert score == 76.0
