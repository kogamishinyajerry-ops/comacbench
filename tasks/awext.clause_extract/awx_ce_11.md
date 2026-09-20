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
Field boundaries: `family` is only the label inside the Category parentheses
before the word "family"; omit the surrounding category text and the word "family".
`clause_no` is the Section identifier, including the § symbol and the complete
number; omit the title after the dash.

## Requirement card

---
Document: ACX-CONTROL-110
Section: §2.83 — 操纵面与配平能力
Category: structural certification requirements (control family)

Text: For the configurations listed in the applicability table, the design
load envelope shall sustain a positive limit load factor of 2.49
and a negative limit load factor of -0.68 without
detrimental permanent deformation. Repeated application up to
1000 action cycles shall be considered. The occurrence
probabilities used in this section shall not exceed 3.7
per flight hour. Compliance shall be shown by: analysis, simulation.
Applicability: fuselage, landing-gear.
As amended: Amendment 2022.
---
