# Certification traceability extraction

Read the three document excerpts and respond with ONE ```json code block
containing EXACTLY these fields (no extra fields):

{
  "requirement_id": string,
  "clause_ref": string,
  "evidence_ids": sorted list of strings (ascending),
  "verified_params": sorted list of strings,
  "test_only_params": sorted list of strings,
  "coverage_complete": boolean
}

Rules: evidence_ids = every evidence document id cited by or citing the
requirement; verified_params = parameters covered by BOTH the test report and
the analysis note; test_only_params = covered by the test report but NOT the
analysis note; coverage_complete = every parameter listed in the requirement
is in verified_params.

## Requirement

---
SPEC-26: The system shall verify PARAM_A9, PARAM_B8, PARAM_C7, PARAM_D7 per §25.312.
Compliance evidence: see TR-56 and AN-4.
---

## Test report

---
TR-56: covers PARAM_A9, PARAM_B8, PARAM_C7, PARAM_D7 at representative conditions.
---

## Analysis note

---
AN-4: analytical verification of PARAM_D7.
---
