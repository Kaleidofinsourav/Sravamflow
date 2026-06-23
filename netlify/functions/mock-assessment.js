function scoreFromFile(file, offset = 0) {
  const size = Number(file.size || 0);
  return Math.max(55, Math.min(92, 70 + ((size + offset) % 23)));
}

function assessFile(file, index = 0) {
  const lowerName = String(file.name || "").toLowerCase();
  const notes = String(file.notes || "").toLowerCase();
  const isCattle = lowerName.includes("cattle") || notes.includes("cattle");

  if (isCattle) {
    return {
      identified_asset_type: "cattle",
      identified_asset_confidence: 0.7,
      overall_confidence_score: 72,
      assessment_confidence: 0.68,
      shop_scorecard: null,
      red_flags: ["MOCK_PROVIDER"],
      guardrail_notes: [
        "Netlify demo mode does not truly inspect image semantics.",
        "Use the FastAPI service with a real vision provider before underwriting decisions."
      ],
      explanation: ["Demo response: filename or notes indicate cattle."]
    };
  }

  const score = scoreFromFile(file, index);
  return {
    identified_asset_type: "shop",
    identified_asset_confidence: 0.7,
    overall_confidence_score: 74,
    assessment_confidence: 0.68,
    shop_scorecard: {
      inventory_score: score,
      footfall_signal_score: Math.max(0, score - 14),
      shop_condition_score: Math.max(0, score - 5),
      business_vintage_signal_score: Math.max(0, score - 10),
      shop_genuineness_score: Math.max(0, score - 3),
      operational_activity_score: Math.max(0, score - 8)
    },
    red_flags: ["MOCK_PROVIDER"],
    guardrail_notes: [
      "Netlify demo mode does not truly inspect image semantics.",
      "Use the FastAPI service with a real vision provider before underwriting decisions."
    ],
    explanation: ["Demo response generated for hosted UI flow testing without external model calls."]
  };
}

function jsonResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      "content-type": "application/json; charset=utf-8"
    },
    body: JSON.stringify(body)
  };
}

module.exports = {
  assessFile,
  jsonResponse
};
