const { assessFile, jsonResponse } = require("./mock-assessment");
const crypto = require("node:crypto");

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return jsonResponse(405, { error: "method not allowed" });
  }

  try {
    const payload = JSON.parse(event.body || "{}");
    const file = payload.file || {};
    const requestId = payload.request_id || crypto.randomUUID();
    const result = assessFile({ ...file, notes: payload.metadata?.notes || "" });

    return jsonResponse(200, {
      request_id: requestId,
      decision: "SCORED",
      result,
      explanation: result.explanation
    });
  } catch (error) {
    return jsonResponse(400, { error: String(error) });
  }
};
