# Sravamflow

## Visual Underwriting HTTP Service

This service exposes the visual credit-underwriting agent over HTTP for ki Credit
backend calls when an FO submits a shop or cattle image from the Agent App.

### Run locally

```bash
pip install -e ".[dev]"
export VISUAL_UNDERWRITING_ANTHROPIC_API_KEY="..."
uvicorn visual_underwriting.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/` or `http://localhost:8000/ui` in a browser to use
the upload UI. The page lets you choose shop vs cattle, select an image, enter
metadata, submit to the API, and view the decision, weighted score, confidence,
fraud flags, and raw JSON response.

Useful configuration:

| Environment variable | Default | Description |
| --- | --- | --- |
| `VISUAL_UNDERWRITING_ANTHROPIC_API_KEY` | unset | Anthropic API key. |
| `VISUAL_UNDERWRITING_ANTHROPIC_MODEL` | `claude-3-5-sonnet-latest` | Vision-capable Anthropic model. |
| `VISUAL_UNDERWRITING_ANTHROPIC_TIMEOUT_SECONDS` | `20` | Anthropic request timeout. |
| `VISUAL_UNDERWRITING_ANTHROPIC_MAX_RETRIES` | `2` | Retry count after a failed model call or malformed model output. |
| `VISUAL_UNDERWRITING_MAX_IMAGE_BYTES` | `5242880` | Maximum upload size. |
| `VISUAL_UNDERWRITING_GEOFENCE_RADIUS_METERS` | `500` | Captured-vs-declared GPS radius. |
| `VISUAL_UNDERWRITING_LOW_CONFIDENCE_THRESHOLD` | `0.65` | Below this, route to manual review. |
| `VISUAL_UNDERWRITING_IMAGE_HASH_STORAGE` | `memory` | Use `redis` for Redis-backed duplicate-image detection. |
| `VISUAL_UNDERWRITING_REDIS_URL` | `redis://localhost:6379/0` | Redis URL when Redis storage is enabled. |

### Endpoints

Both endpoints accept `multipart/form-data`:

- `image`: the image file. The service validates size and detects image MIME
  type from magic bytes.
- `metadata`: JSON string with:
  `captured_lat`, `captured_lng`, `declared_lat`, `declared_lng`,
  `captured_at`, `declared_business_hours`, and `declared_cattle_count`.
- Optional `X-Request-ID` header for caller-provided correlation.

#### Shop scoring

```bash
curl -X POST "http://localhost:8000/v1/underwriting/shop" \
  -H "X-Request-ID: app-req-123" \
  -F "image=@./shop.jpg;type=image/jpeg" \
  -F 'metadata={
    "captured_lat": 12.9716,
    "captured_lng": 77.5946,
    "declared_lat": 12.9717,
    "declared_lng": 77.5947,
    "captured_at": "2026-06-23T10:00:00Z",
    "declared_business_hours": "09:00-18:00",
    "declared_cattle_count": null
  }'
```

#### Cattle scoring

```bash
curl -X POST "http://localhost:8000/v1/underwriting/cattle" \
  -H "X-Request-ID: app-req-456" \
  -F "image=@./cattle.jpg;type=image/jpeg" \
  -F 'metadata={
    "captured_lat": 12.9716,
    "captured_lng": 77.5946,
    "declared_lat": 12.9717,
    "declared_lng": 77.5947,
    "captured_at": "2026-06-23T10:00:00Z",
    "declared_business_hours": "09:00-18:00",
    "declared_cattle_count": 3
  }'
```

### Sample responses

`SCORED` and `REFER_TO_MANUAL_REVIEW` are both successful business outcomes and
return HTTP 200.

#### SCORED

```json
{
  "request_id": "app-req-123",
  "asset_type": "shop",
  "decision": "SCORED",
  "weighted_score": 74.5,
  "confidence": 0.91,
  "fraud_flags": [],
  "explanation": ["Visual evidence supports automated scoring."],
  "model_result": {
    "score_components": {
      "asset_presence": 85,
      "asset_quality": 70,
      "context_consistency": 75,
      "repayment_capacity_signal": 65
    },
    "confidence": 0.91,
    "fraud_flags": [],
    "observed_cattle_count": null,
    "explanation": ["Visual evidence supports automated scoring."]
  }
}
```

#### REFER_TO_MANUAL_REVIEW

```json
{
  "request_id": "app-req-456",
  "asset_type": "cattle",
  "decision": "REFER_TO_MANUAL_REVIEW",
  "weighted_score": 68.0,
  "confidence": 0.42,
  "fraud_flags": [
    {
      "code": "LOW_VISION_CONFIDENCE",
      "severity": "SOFT",
      "message": "Vision model confidence 0.42 is below configured threshold 0.65."
    }
  ],
  "explanation": ["Image is partially obstructed; route to manual review."],
  "model_result": {
    "score_components": {
      "asset_presence": 80,
      "asset_quality": 60,
      "context_consistency": 70,
      "repayment_capacity_signal": 60
    },
    "confidence": 0.42,
    "fraud_flags": [],
    "observed_cattle_count": 3,
    "explanation": ["Image is partially obstructed; route to manual review."]
  }
}
```

Bad JSON metadata and non-image uploads return HTTP 400. Pydantic validation
errors return HTTP 422.
