# Sravamflow

## Visual Underwriting HTTP Service

This service exposes the visual credit-underwriting agent over HTTP for ki Credit
backend calls when an FO submits a shop or cattle image from the Agent App.

### Run locally

```bash
pip install -e ".[dev]"
cp .env.example .env
# Default local/demo mode uses VISUAL_UNDERWRITING_VISION_PROVIDER=mock.
uvicorn visual_underwriting.main:app --host 0.0.0.0 --port 8000
```

### Editable prompt and key structure

Keys and runtime settings live in:

```text
.env
```

Start from:

```bash
cp .env.example .env
```

The prompts live in markdown files:

```text
visual_underwriting/prompts/underwriting_score.md   # production shop/cattle scoring prompt
visual_underwriting/prompts/visual_assessment.md    # image-first UI assessment prompt
```

To change model behavior:

1. Edit the relevant markdown prompt file.
2. Restart/redeploy the service.
3. Test again from `http://localhost:8000/ui`.

The prompt files support these placeholders:

- `{{asset_type}}` for shop/cattle production scoring.
- `{{metadata_json}}` for request metadata/context.
- `{{schema_json}}` for the strict Pydantic JSON schema the model must return.

### Model provider for testing

Cursor chat/IDE models such as Opus or GPT are not available as a runtime API
that this FastAPI service can call after deployment. For local UI testing without
external model keys, use the built-in mock provider:

```env
VISUAL_UNDERWRITING_VISION_PROVIDER=mock
```

Mock mode lets the upload UI and API flow work without Anthropic/Sarvam calls,
but it does not truly interpret the image. It returns a clearly marked
`MOCK_PROVIDER` red flag and deterministic demo scores.

For real image understanding, switch to:

```env
VISUAL_UNDERWRITING_VISION_PROVIDER=anthropic
VISUAL_UNDERWRITING_ANTHROPIC_API_KEY=...
```

Open `http://localhost:8000/` or `http://localhost:8000/ui` in a browser to use
the image-first assessment UI. The page lets you upload an image without choosing
shop/cattle first. The agent identifies what it sees and returns:

- identified asset type and identification confidence
- overall visual confidence score
- inventory score
- footfall signal score
- shop condition score
- business vintage signal score
- shop genuineness score
- operational activity score
- guardrail notes, red flags, and the raw JSON response

Useful configuration:

| Environment variable | Default | Description |
| --- | --- | --- |
| `VISUAL_UNDERWRITING_ANTHROPIC_API_KEY` | unset | Anthropic API key. |
| `VISUAL_UNDERWRITING_VISION_PROVIDER` | `mock` | `mock` for local UI tests without model API calls, `anthropic` for real vision scoring. |
| `VISUAL_UNDERWRITING_ANTHROPIC_MODEL` | `claude-3-5-sonnet-latest` | Vision-capable Anthropic model. |
| `VISUAL_UNDERWRITING_ANTHROPIC_TIMEOUT_SECONDS` | `20` | Anthropic request timeout. |
| `VISUAL_UNDERWRITING_ANTHROPIC_MAX_RETRIES` | `2` | Retry count after a failed model call or malformed model output. |
| `VISUAL_UNDERWRITING_MAX_IMAGE_BYTES` | `5242880` | Maximum upload size. |
| `VISUAL_UNDERWRITING_GEOFENCE_RADIUS_METERS` | `500` | Captured-vs-declared GPS radius. |
| `VISUAL_UNDERWRITING_LOW_CONFIDENCE_THRESHOLD` | `0.65` | Below this, route to manual review. |
| `VISUAL_UNDERWRITING_IMAGE_HASH_STORAGE` | `memory` | Use `redis` for Redis-backed duplicate-image detection. |
| `VISUAL_UNDERWRITING_REDIS_URL` | `redis://localhost:6379/0` | Redis URL when Redis storage is enabled. |
| `VISUAL_UNDERWRITING_UNDERWRITING_PROMPT_PATH` | `visual_underwriting/prompts/underwriting_score.md` | Markdown prompt for shop/cattle scoring. |
| `VISUAL_UNDERWRITING_ASSESSMENT_PROMPT_PATH` | `visual_underwriting/prompts/visual_assessment.md` | Markdown prompt for image-first UI assessment. |

### Endpoints

Both endpoints accept `multipart/form-data`:

- `image`: the image file. The service validates size and detects image MIME
  type from magic bytes.
- `metadata`: JSON string with:
  `captured_lat`, `captured_lng`, `declared_lat`, `declared_lng`,
  `captured_at`, `declared_business_hours`, and `declared_cattle_count`.
- Optional `X-Request-ID` header for caller-provided correlation.

#### Image-first visual assessment

Use this endpoint for the browser lab UI. It requires only an image and optional
metadata/context notes. It does not replace the production shop/cattle
underwriting endpoints below.

```bash
curl -X POST "http://localhost:8000/v1/underwriting/assess" \
  -H "X-Request-ID: lab-req-123" \
  -F "image=@./shop.jpg;type=image/jpeg" \
  -F 'metadata={"notes":"FO submitted this as a shop image."}'
```

Sample response:

```json
{
  "request_id": "lab-req-123",
  "decision": "SCORED",
  "result": {
    "identified_asset_type": "shop",
    "identified_asset_confidence": 0.94,
    "overall_confidence_score": 82,
    "assessment_confidence": 0.88,
    "shop_scorecard": {
      "inventory_score": 80,
      "footfall_signal_score": 70,
      "shop_condition_score": 85,
      "business_vintage_signal_score": 75,
      "shop_genuineness_score": 90,
      "operational_activity_score": 78
    },
    "red_flags": [],
    "guardrail_notes": ["Scores are based only on visible evidence."],
    "explanation": ["The image appears to show an operating retail shop."]
  },
  "explanation": ["The image appears to show an operating retail shop."]
}
```

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
