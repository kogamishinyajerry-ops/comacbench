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
Copy `clause_ref` verbatim from the requirement, including the § symbol and
the complete clause number; omit the sentence-ending punctuation.

## Requirement

---
SPEC-12: The system shall verify PARAM_A3, PARAM_B6 per §25.455.
Compliance evidence: see TR-91 and AN-8.
---

## Test report

---
TR-91: covers PARAM_A3 at representative conditions.
---

## Analysis note

---
AN-8: analytical verification of PARAM_A3.
---
