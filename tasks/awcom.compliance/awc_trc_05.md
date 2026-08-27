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
SPEC-34: The system shall verify PARAM_A2, PARAM_B1 per §25.444.
Compliance evidence: see TR-67 and AN-9.
---

## Test report

---
TR-67: covers PARAM_A2, PARAM_B1 at representative conditions.
---

## Analysis note

---
AN-9: analytical verification of PARAM_B1.
---
