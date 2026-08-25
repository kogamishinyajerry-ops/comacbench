# Structured extraction from a requirement card

Read the requirement card below and respond with ONE ```json code block
containing EXACTLY these fields (no extra fields):

{
  "family": string,
  "clause_no": string,
  "positive_load_limit": number,
  "negative_load_limit": number,
  "cycles_or_actions": integer,
  "probability_per_hour": number,
  "applies_to": sorted list of strings (ascending),
  "compliance_methods": sorted list of strings (ascending),
  "amendment_year": integer
}

Rules: copy values verbatim from the card (numbers as numbers); sort the two
list fields ascending (string sort); do not add commentary outside the JSON.

## Requirement card

---
Document: ACX-STALL-111
Section: §3.97 — 失速特性与最小速度
Category: structural certification requirements (stall family)

Text: For the configurations listed in the applicability table, the design
load envelope shall sustain a positive limit load factor of 3.42
and a negative limit load factor of -0.66 without
detrimental permanent deformation. Repeated application up to
2000 action cycles shall be considered. The occurrence
probabilities used in this section shall not exceed 1.4
per flight hour. Compliance shall be shown by: simulation, test.
Applicability: engine-mount, fuselage.
As amended: Amendment 2016.
---
