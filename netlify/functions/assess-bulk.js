const { assessFile, jsonResponse } = require("./mock-assessment");
const crypto = require("node:crypto");

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return jsonResponse(405, { error: "method not allowed" });
  }

  try {
    const payload = JSON.parse(event.body || "{}");
    const requestId = payload.request_id || crypto.randomUUID();
    const metadata = payload.metadata || {};
    const files = Array.isArray(payload.files) ? payload.files : [];

    const items = files.map((file, index) => {
      const result = assessFile({ ...file, notes: metadata.notes || "" }, index);
      return {
        filename: file.name || `image-${index + 1}`,
        status_code: 200,
        response: {
          request_id: `${requestId}-${index + 1}`,
          decision: "SCORED",
          result,
          explanation: result.explanation
        },
        error: null
      };
    });

    return jsonResponse(200, {
      request_id: requestId,
      total: items.length,
      succeeded: items.length,
      failed: 0,
      items
    });
  } catch (error) {
    return jsonResponse(400, { error: String(error) });
  }
};
