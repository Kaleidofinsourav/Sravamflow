def render_underwriting_ui() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Visual Underwriting</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f7fb;
      color: #172033;
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 32px; }
    main { max-width: 1120px; margin: 0 auto; }
    header { margin-bottom: 24px; }
    h1 { margin: 0 0 8px; font-size: 32px; }
    p { color: #536079; line-height: 1.5; }
    .grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr); gap: 24px; }
    .card {
      background: #fff;
      border: 1px solid #dfe4ef;
      border-radius: 18px;
      box-shadow: 0 18px 45px rgba(25, 35, 60, 0.08);
      padding: 24px;
    }
    label { display: block; font-weight: 650; font-size: 13px; margin-bottom: 6px; color: #27324a; }
    input, select {
      width: 100%;
      border: 1px solid #cfd6e6;
      border-radius: 10px;
      padding: 11px 12px;
      font: inherit;
      background: #fff;
    }
    input:focus, select:focus {
      outline: 3px solid rgba(47, 111, 237, 0.16);
      border-color: #2f6fed;
    }
    .fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
    .full { grid-column: 1 / -1; }
    button {
      border: 0;
      border-radius: 12px;
      padding: 13px 18px;
      background: #2f6fed;
      color: #fff;
      font-weight: 750;
      cursor: pointer;
      width: 100%;
      margin-top: 18px;
    }
    button:disabled { opacity: 0.65; cursor: wait; }
    .preview {
      display: none;
      width: 100%;
      max-height: 320px;
      object-fit: contain;
      border-radius: 14px;
      border: 1px solid #dfe4ef;
      background: #f8f9fc;
      margin-top: 10px;
    }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 8px 12px;
      font-weight: 800;
      font-size: 13px;
      background: #eef2ff;
      color: #2f4fbb;
    }
    .status.scored { background: #eaf8ef; color: #16713a; }
    .status.manual { background: #fff4e6; color: #a55a00; }
    .metric { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }
    .metric div { background: #f7f8fb; border-radius: 14px; padding: 16px; }
    .metric span { display: block; color: #6a7489; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .metric strong { display: block; font-size: 30px; margin-top: 6px; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #111827;
      color: #e5e7eb;
      padding: 16px;
      border-radius: 14px;
      overflow: auto;
      min-height: 180px;
    }
    .error { color: #b42318; font-weight: 700; }
    .help { font-size: 12px; color: #6a7489; margin-top: 6px; }
    @media (max-width: 860px) {
      body { padding: 18px; }
      .grid, .fields, .metric { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Visual Underwriting</h1>
      <p>Upload a shop or cattle image, enter capture metadata, and submit it to the underwriting service for a confidence result.</p>
    </header>
    <section class="grid">
      <form id="underwriting-form" class="card">
        <div class="fields">
          <div>
            <label for="asset_type">Submission type</label>
            <select id="asset_type" name="asset_type">
              <option value="shop">Shop</option>
              <option value="cattle">Cattle</option>
            </select>
          </div>
          <div>
            <label for="request_id">Request ID</label>
            <input id="request_id" name="request_id" placeholder="optional correlation id">
          </div>
          <div class="full">
            <label for="image">Image</label>
            <input id="image" name="image" type="file" accept="image/*" required>
            <div class="help">The API validates the actual image bytes, not just the filename.</div>
            <img id="preview" class="preview" alt="Selected upload preview">
          </div>
          <div>
            <label for="captured_lat">Captured latitude</label>
            <input id="captured_lat" type="number" step="any" required value="12.9716">
          </div>
          <div>
            <label for="captured_lng">Captured longitude</label>
            <input id="captured_lng" type="number" step="any" required value="77.5946">
          </div>
          <div>
            <label for="declared_lat">Declared latitude</label>
            <input id="declared_lat" type="number" step="any" required value="12.9717">
          </div>
          <div>
            <label for="declared_lng">Declared longitude</label>
            <input id="declared_lng" type="number" step="any" required value="77.5947">
          </div>
          <div>
            <label for="captured_at">Captured at</label>
            <input id="captured_at" type="datetime-local" required>
          </div>
          <div>
            <label for="declared_business_hours">Declared business hours</label>
            <input id="declared_business_hours" required value="09:00-18:00">
          </div>
          <div id="cattle-count-field">
            <label for="declared_cattle_count">Declared cattle count</label>
            <input id="declared_cattle_count" type="number" min="0" step="1" value="3">
          </div>
        </div>
        <button id="submit-button" type="submit">Run visual underwriting</button>
      </form>
      <aside class="card">
        <div id="summary">
          <span class="status">Waiting for submission</span>
          <div class="metric">
            <div><span>Decision</span><strong>-</strong></div>
            <div><span>Confidence</span><strong>-</strong></div>
          </div>
        </div>
        <h2>Response</h2>
        <pre id="response">{}</pre>
      </aside>
    </section>
  </main>
  <script>
    const form = document.getElementById("underwriting-form");
    const assetType = document.getElementById("asset_type");
    const imageInput = document.getElementById("image");
    const preview = document.getElementById("preview");
    const submitButton = document.getElementById("submit-button");
    const responseBox = document.getElementById("response");
    const summary = document.getElementById("summary");
    const cattleCountField = document.getElementById("cattle-count-field");
    const cattleCountInput = document.getElementById("declared_cattle_count");
    const capturedAt = document.getElementById("captured_at");

    capturedAt.value = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 16);

    function updateCattleVisibility() {
      const isCattle = assetType.value === "cattle";
      cattleCountField.style.display = isCattle ? "block" : "none";
      cattleCountInput.required = isCattle;
    }

    function toIsoFromLocalDateTime(value) {
      return new Date(value).toISOString();
    }

    function metadataPayload() {
      const isCattle = assetType.value === "cattle";
      return {
        captured_lat: Number(document.getElementById("captured_lat").value),
        captured_lng: Number(document.getElementById("captured_lng").value),
        declared_lat: Number(document.getElementById("declared_lat").value),
        declared_lng: Number(document.getElementById("declared_lng").value),
        captured_at: toIsoFromLocalDateTime(capturedAt.value),
        declared_business_hours: document.getElementById("declared_business_hours").value,
        declared_cattle_count: isCattle ? Number(cattleCountInput.value) : null
      };
    }

    function renderSummary(data) {
      const statusClass = data.decision === "SCORED" ? "scored" : "manual";
      const confidence = data.confidence === null || data.confidence === undefined
        ? "-"
        : `${Math.round(data.confidence * 100)}%`;
      summary.innerHTML = `
        <span class="status ${statusClass}">${data.decision}</span>
        <div class="metric">
          <div><span>Weighted score</span><strong>${data.weighted_score ?? "-"}</strong></div>
          <div><span>Confidence</span><strong>${confidence}</strong></div>
        </div>
      `;
    }

    function renderError(message, detail) {
      summary.innerHTML = `
        <span class="status manual">Request failed</span>
        <p class="error">${message}</p>
      `;
      responseBox.textContent = JSON.stringify(detail, null, 2);
    }

    assetType.addEventListener("change", updateCattleVisibility);
    imageInput.addEventListener("change", () => {
      const file = imageInput.files[0];
      if (!file) {
        preview.style.display = "none";
        preview.removeAttribute("src");
        return;
      }
      preview.src = URL.createObjectURL(file);
      preview.style.display = "block";
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      submitButton.disabled = true;
      submitButton.textContent = "Scoring...";
      responseBox.textContent = "Submitting...";

      const formData = new FormData();
      formData.append("image", imageInput.files[0]);
      formData.append("metadata", JSON.stringify(metadataPayload()));

      const headers = {};
      const requestId = document.getElementById("request_id").value.trim();
      if (requestId) {
        headers["X-Request-ID"] = requestId;
      }

      try {
        const response = await fetch(`/v1/underwriting/${assetType.value}`, {
          method: "POST",
          headers,
          body: formData
        });
        const data = await response.json();
        responseBox.textContent = JSON.stringify(data, null, 2);
        if (!response.ok) {
          renderError(`HTTP ${response.status}`, data);
          return;
        }
        renderSummary(data);
      } catch (error) {
        renderError("Network or browser error", { error: String(error) });
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Run visual underwriting";
      }
    });

    updateCattleVisibility();
  </script>
</body>
</html>
"""
