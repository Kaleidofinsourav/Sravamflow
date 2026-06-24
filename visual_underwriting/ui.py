def render_underwriting_ui() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Visual Underwriting Lab</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f3f6fb;
      color: #152033;
    }
    * { box-sizing: border-box; }
    body { margin: 0; padding: 28px; }
    main { max-width: 1240px; margin: 0 auto; }
    header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 18px;
      margin-bottom: 22px;
    }
    h1 { margin: 0 0 8px; font-size: 34px; letter-spacing: -0.03em; }
    h2 { margin: 0 0 14px; }
    p { color: #5d687c; line-height: 1.5; margin: 0; }
    .badge {
      background: #e9f0ff;
      color: #2f5dcc;
      border-radius: 999px;
      padding: 9px 13px;
      font-weight: 800;
      font-size: 13px;
      white-space: nowrap;
    }
    .grid { display: grid; grid-template-columns: minmax(340px, 0.82fr) minmax(420px, 1fr); gap: 22px; }
    .card {
      background: #fff;
      border: 1px solid #dce3ef;
      border-radius: 22px;
      box-shadow: 0 20px 50px rgba(23, 35, 61, 0.08);
      padding: 22px;
    }
    label { display: block; font-weight: 750; font-size: 13px; margin: 0 0 7px; color: #25304a; }
    input, textarea {
      width: 100%;
      border: 1px solid #ccd5e5;
      border-radius: 12px;
      padding: 12px 13px;
      font: inherit;
      background: #fff;
    }
    textarea { min-height: 86px; resize: vertical; }
    input:focus, textarea:focus {
      outline: 3px solid rgba(47, 111, 237, 0.16);
      border-color: #2f6fed;
    }
    .fields { display: grid; gap: 16px; }
    .optional-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .preview-wrap {
      display: grid;
      place-items: center;
      align-content: center;
      min-height: 320px;
      border: 1px dashed #b9c5d9;
      border-radius: 18px;
      background: #f8faff;
      overflow: hidden;
    }
    .preview {
      display: none;
      width: 100%;
      max-height: 440px;
      object-fit: contain;
      background: #f8faff;
    }
    .preview-grid {
      display: none;
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
      gap: 10px;
      width: 100%;
      padding: 12px;
    }
    .preview-tile {
      background: #fff;
      border: 1px solid #dce3ef;
      border-radius: 14px;
      overflow: hidden;
    }
    .preview-tile img {
      width: 100%;
      height: 96px;
      object-fit: cover;
      display: block;
      background: #eef3fb;
    }
    .preview-tile span {
      display: block;
      padding: 8px;
      font-size: 11px;
      font-weight: 750;
      color: #536079;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .empty-preview { color: #71809b; font-weight: 700; text-align: center; padding: 18px; }
    button {
      border: 0;
      border-radius: 14px;
      padding: 14px 18px;
      background: linear-gradient(135deg, #2f6fed, #6045e8);
      color: #fff;
      font-weight: 850;
      cursor: pointer;
      width: 100%;
      margin-top: 4px;
      box-shadow: 0 12px 24px rgba(47, 111, 237, 0.24);
    }
    button:disabled { opacity: 0.68; cursor: wait; }
    .help { font-size: 12px; color: #6b778f; margin-top: 7px; }
    .status-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 16px; }
    .status {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 8px 12px;
      font-weight: 850;
      font-size: 13px;
      background: #eef2ff;
      color: #3153bd;
    }
    .status.scored { background: #eaf8ef; color: #16713a; }
    .status.manual { background: #fff4e6; color: #a55a00; }
    .hero-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 16px 0 18px; }
    .metric, .score-card {
      background: #f7f9fd;
      border: 1px solid #edf1f7;
      border-radius: 16px;
      padding: 15px;
    }
    .metric span, .score-card span {
      display: block;
      color: #6a758d;
      font-size: 11px;
      font-weight: 850;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .metric strong {
      display: block;
      margin-top: 5px;
      font-size: 28px;
      letter-spacing: -0.03em;
    }
    .score-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }
    .score-value { display: flex; align-items: baseline; gap: 4px; margin-top: 7px; }
    .score-value strong { font-size: 26px; letter-spacing: -0.03em; }
    .bar { height: 8px; background: #e3e8f2; border-radius: 999px; overflow: hidden; margin-top: 10px; }
    .bar div { height: 100%; width: 0%; background: linear-gradient(90deg, #2f6fed, #19a76f); border-radius: inherit; }
    ul { margin: 8px 0 0; padding-left: 20px; color: #4f5b70; }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: #101827;
      color: #e6edf6;
      padding: 16px;
      border-radius: 16px;
      overflow: auto;
      min-height: 170px;
      margin-bottom: 0;
    }
    .error { color: #b42318; font-weight: 800; }
    .muted { color: #6a758d; }
    .bulk-list { display: grid; gap: 12px; margin-top: 12px; }
    .bulk-item {
      background: #f7f9fd;
      border: 1px solid #edf1f7;
      border-radius: 16px;
      padding: 14px;
    }
    .bulk-item h3 {
      margin: 0 0 10px;
      font-size: 15px;
      word-break: break-word;
    }
    .bulk-meta { display: flex; flex-wrap: wrap; gap: 8px; }
    @media (max-width: 930px) {
      body { padding: 18px; }
      header { display: block; }
      .badge { display: inline-flex; margin-top: 12px; }
      .grid, .hero-metrics, .score-grid, .optional-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Visual Underwriting Lab</h1>
        <p>Upload one or many field images. The agent identifies what it sees and returns visual confidence plus business-quality signals.</p>
      </div>
      <span class="badge">Image-first agent assessment</span>
    </header>

    <section class="grid">
      <form id="assessment-form" class="card">
        <div class="fields">
          <div>
            <label for="image">Upload image/images</label>
            <input id="image" name="image" type="file" accept="image/*" multiple required>
            <div class="help">Select one image for single assessment or multiple images for bulk upload.</div>
          </div>

          <div class="preview-wrap">
            <div id="empty-preview" class="empty-preview">Image previews will appear here</div>
            <div id="preview-grid" class="preview-grid"></div>
          </div>

          <div>
            <label for="request_id">Request ID</label>
            <input id="request_id" placeholder="optional correlation id">
          </div>

          <div>
            <label for="notes">Optional context / guardrail notes</label>
            <textarea id="notes" placeholder="Example: FO submitted this as a kirana shop image. Do not enter private customer data."></textarea>
          </div>

          <details>
            <summary class="muted">Optional capture metadata</summary>
            <div class="optional-grid" style="margin-top: 12px;">
              <div>
                <label for="captured_lat">Captured latitude</label>
                <input id="captured_lat" type="number" step="any" placeholder="optional">
              </div>
              <div>
                <label for="captured_lng">Captured longitude</label>
                <input id="captured_lng" type="number" step="any" placeholder="optional">
              </div>
              <div>
                <label for="captured_at">Captured at</label>
                <input id="captured_at" type="datetime-local">
              </div>
            </div>
          </details>

          <button id="submit-button" type="submit">Identify & score image(s)</button>
        </div>
      </form>

      <aside class="card">
        <div id="summary">
          <div class="status-row">
            <span class="status">Waiting for image</span>
          </div>
          <div class="hero-metrics">
            <div class="metric"><span>Identified as</span><strong>-</strong></div>
            <div class="metric"><span>Overall confidence</span><strong>-</strong></div>
            <div class="metric"><span>Assessment confidence</span><strong>-</strong></div>
          </div>
        </div>

        <h2>Business visual scorecard</h2>
        <div id="score-grid" class="score-grid">
          <p class="muted">Run an assessment to see inventory, footfall, shop condition, vintage, genuineness, and activity scores.</p>
        </div>

        <h2 style="margin-top: 22px;">Raw response</h2>
        <pre id="response">{}</pre>
      </aside>
    </section>
  </main>

  <script>
    const form = document.getElementById("assessment-form");
    const imageInput = document.getElementById("image");
    const previewGrid = document.getElementById("preview-grid");
    const emptyPreview = document.getElementById("empty-preview");
    const submitButton = document.getElementById("submit-button");
    const responseBox = document.getElementById("response");
    const summary = document.getElementById("summary");
    const scoreGrid = document.getElementById("score-grid");

    const scoreLabels = {
      inventory_score: "Inventory",
      footfall_signal_score: "Footfall signal",
      shop_condition_score: "Shop condition",
      business_vintage_signal_score: "Vintage signal",
      shop_genuineness_score: "Looks genuine",
      operational_activity_score: "Operational activity"
    };

    function optionalNumber(id) {
      const value = document.getElementById(id).value;
      return value === "" ? undefined : Number(value);
    }

    function metadataPayload() {
      const payload = {};
      const lat = optionalNumber("captured_lat");
      const lng = optionalNumber("captured_lng");
      const capturedAt = document.getElementById("captured_at").value;
      const notes = document.getElementById("notes").value.trim();

      if (lat !== undefined) payload.captured_lat = lat;
      if (lng !== undefined) payload.captured_lng = lng;
      if (capturedAt) payload.captured_at = new Date(capturedAt).toISOString();
      if (notes) payload.notes = notes;

      return payload;
    }

    function percentFromUnit(value) {
      return value === null || value === undefined ? "-" : `${Math.round(value * 100)}%`;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderScoreCard(key, value) {
      const safeValue = value ?? 0;
      return `
        <div class="score-card">
          <span>${scoreLabels[key]}</span>
          <div class="score-value"><strong>${safeValue}</strong><small>/100</small></div>
          <div class="bar"><div style="width: ${Math.max(0, Math.min(100, safeValue))}%"></div></div>
        </div>
      `;
    }

    function renderSummary(data) {
      const result = data.result;
      const isManual = data.decision === "REFER_TO_MANUAL_REVIEW";
      const statusClass = isManual ? "manual" : "scored";

      if (!result) {
        summary.innerHTML = `
          <div class="status-row"><span class="status ${statusClass}">${data.decision}</span></div>
          <p class="muted">${(data.explanation || []).join(" ")}</p>
        `;
        scoreGrid.innerHTML = `<p class="muted">No scorecard returned. Route this image to manual review.</p>`;
        return;
      }

      summary.innerHTML = `
        <div class="status-row">
          <span class="status ${statusClass}">${data.decision}</span>
          <span class="status">Detected: ${result.identified_asset_type}</span>
        </div>
        <div class="hero-metrics">
          <div class="metric"><span>Identified as</span><strong>${result.identified_asset_type}</strong></div>
          <div class="metric"><span>Overall confidence</span><strong>${result.overall_confidence_score}</strong></div>
          <div class="metric"><span>Assessment confidence</span><strong>${percentFromUnit(result.assessment_confidence)}</strong></div>
        </div>
        ${(result.red_flags || []).length ? `<h2>Red flags</h2><ul>${result.red_flags.map(flag => `<li>${flag}</li>`).join("")}</ul>` : ""}
        ${(result.guardrail_notes || []).length ? `<h2 style="margin-top: 18px;">Guardrail notes</h2><ul>${result.guardrail_notes.map(note => `<li>${note}</li>`).join("")}</ul>` : ""}
      `;

      if (!result.shop_scorecard) {
        scoreGrid.innerHTML = `<p class="muted">Image was not identified as a shop, so shop scorecard is not applicable.</p>`;
        return;
      }

      scoreGrid.innerHTML = Object.entries(result.shop_scorecard)
        .map(([key, value]) => renderScoreCard(key, value))
        .join("");
    }

    function renderBulkSummary(data) {
      summary.innerHTML = `
        <div class="status-row">
          <span class="status scored">Bulk assessment complete</span>
        </div>
        <div class="hero-metrics">
          <div class="metric"><span>Total images</span><strong>${data.total}</strong></div>
          <div class="metric"><span>Succeeded</span><strong>${data.succeeded}</strong></div>
          <div class="metric"><span>Failed</span><strong>${data.failed}</strong></div>
        </div>
      `;

      scoreGrid.innerHTML = `
        <div class="bulk-list">
          ${data.items.map((item, index) => {
            if (item.error) {
              return `
                <div class="bulk-item">
                  <h3>${index + 1}. ${escapeHtml(item.filename)}</h3>
                  <div class="bulk-meta">
                    <span class="status manual">HTTP ${item.status_code}</span>
                    <span class="status manual">${escapeHtml(item.error)}</span>
                  </div>
                </div>
              `;
            }

            const response = item.response || {};
            const result = response.result || {};
            const scorecard = result.shop_scorecard || {};
            return `
              <div class="bulk-item">
                <h3>${index + 1}. ${escapeHtml(item.filename)}</h3>
                <div class="bulk-meta">
                  <span class="status ${response.decision === "SCORED" ? "scored" : "manual"}">${response.decision || "-"}</span>
                  <span class="status">Detected: ${result.identified_asset_type || "-"}</span>
                  <span class="status">Overall: ${result.overall_confidence_score ?? "-"}</span>
                  <span class="status">Confidence: ${percentFromUnit(result.assessment_confidence)}</span>
                </div>
                ${result.red_flags?.length ? `<ul>${result.red_flags.map(flag => `<li>${escapeHtml(flag)}</li>`).join("")}</ul>` : ""}
                ${result.shop_scorecard ? `
                  <div class="score-grid">
                    ${Object.entries(scorecard).map(([key, value]) => renderScoreCard(key, value)).join("")}
                  </div>
                ` : `<p class="muted">Shop scorecard not applicable.</p>`}
              </div>
            `;
          }).join("")}
        </div>
      `;
    }

    function renderError(message, detail) {
      summary.innerHTML = `
        <div class="status-row"><span class="status manual">Request failed</span></div>
        <p class="error">${message}</p>
      `;
      scoreGrid.innerHTML = `<p class="muted">Fix the input and try again.</p>`;
      responseBox.textContent = JSON.stringify(detail, null, 2);
    }

    imageInput.addEventListener("change", () => {
      const files = Array.from(imageInput.files || []);
      if (!files.length) {
        previewGrid.style.display = "none";
        previewGrid.innerHTML = "";
        emptyPreview.style.display = "block";
        return;
      }
      previewGrid.innerHTML = files.map(file => `
        <div class="preview-tile">
          <img src="${URL.createObjectURL(file)}" alt="${escapeHtml(file.name)} preview">
          <span>${escapeHtml(file.name)}</span>
        </div>
      `).join("");
      previewGrid.style.display = "grid";
      emptyPreview.style.display = "none";
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      submitButton.disabled = true;
      const files = Array.from(imageInput.files || []);
      if (!files.length) {
        renderError("No image selected", { error: "Select at least one image." });
        submitButton.disabled = false;
        return;
      }
      submitButton.textContent = files.length > 1 ? `Assessing ${files.length} images...` : "Assessing image...";
      responseBox.textContent = "Submitting...";

      const formData = new FormData();
      const isBulk = files.length > 1;
      for (const file of files) {
        formData.append(isBulk ? "images" : "image", file);
      }
      formData.append("metadata", JSON.stringify(metadataPayload()));

      const headers = {};
      const requestId = document.getElementById("request_id").value.trim();
      if (requestId) headers["X-Request-ID"] = requestId;

      try {
        const response = await fetch(isBulk ? "/v1/underwriting/assess/bulk" : "/v1/underwriting/assess", {
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
        if (isBulk) {
          renderBulkSummary(data);
        } else {
          renderSummary(data);
        }
      } catch (error) {
        renderError("Network or browser error", { error: String(error) });
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = "Identify & score image(s)";
      }
    });
  </script>
</body>
</html>
"""
