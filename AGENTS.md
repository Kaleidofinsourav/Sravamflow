# Sravamflow

## Cursor Cloud specific instructions

### Project layout
- The product is the **Visual Underwriting HTTP service** (`visual_underwriting/`), a FastAPI app that scores shop/cattle images for credit underwriting via an Anthropic vision model. See `README.md` for endpoints, request/response shapes, and the full config table.
- Application code currently lives on feature branches; the `main` branch may be empty. Don't assume `pyproject.toml`/source files exist on every branch.

### Dev environment
- Python 3.11+ FastAPI service. The startup update script creates a virtualenv at `.venv` and installs the project with dev extras. Activate it with `source .venv/bin/activate` before running tooling.
- Standard commands (do not duplicate elsewhere): tests via `pytest` (config in `pyproject.toml`, `testpaths=tests`); run the app via `uvicorn visual_underwriting.main:app --reload --port 8000` (run command and config documented in `README.md`).
- No linter/formatter is configured in `pyproject.toml`; `pytest` is the only automated check.

### Non-obvious gotchas
- **Startup requires an Anthropic key.** `create_app()` eagerly constructs the Anthropic client, so `uvicorn` will fail to boot unless `VISUAL_UNDERWRITING_ANTHROPIC_API_KEY` (or `ANTHROPIC_API_KEY`) is set. For local dev without a real key, set a dummy value (e.g. `VISUAL_UNDERWRITING_ANTHROPIC_API_KEY=dummy`): the server boots, integrity checks (geofence, duplicate-image, business-hours) and request validation (400/422) work normally, and image-scoring requests degrade gracefully to `decision: REFER_TO_MANUAL_REVIEW` (HTTP 200) once the vision call fails. Provide a **real** Anthropic key to exercise the full `SCORED` path.
- Redis is optional. The default `VISUAL_UNDERWRITING_IMAGE_HASH_STORAGE=memory` needs no external services; only set it to `redis` (with `VISUAL_UNDERWRITING_REDIS_URL`) when a Redis instance is actually available.
