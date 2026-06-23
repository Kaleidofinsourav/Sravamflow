# Image-First Visual Assessment Prompt

Identify whether the image most likely shows a shop, cattle, another asset, or is unknown.

For shop images, produce a visual scorecard using these dimensions only:

- `inventory_score`: visible stock depth, variety, and merchandising quality.
- `footfall_signal_score`: visible customer/staff movement or signs of regular traffic; do not invent people.
- `shop_condition_score`: cleanliness, organization, lighting, signage, and upkeep.
- `business_vintage_signal_score`: visible signs of established operations such as permanent fixtures, aged signage, stocked shelves, or durable setup. Do not claim exact age.
- `shop_genuineness_score`: whether the scene looks like a real operating shop rather than staged/fake.
- `operational_activity_score`: visible indicators that the business is active/open and ready to trade.

For non-shop images, set `shop_scorecard` to null and explain why.

Guardrails:

- Use only visual evidence.
- Do not infer revenue, profit, repayment capacity, identity, caste, religion, gender, age, or other protected/sensitive attributes.
- If evidence is unclear, lower confidence and explain uncertainty in `guardrail_notes`.
- Return strict JSON only. Do not include markdown fences or commentary outside the JSON object.

Optional metadata JSON:

{{metadata_json}}

Return JSON matching exactly this schema:

{{schema_json}}
