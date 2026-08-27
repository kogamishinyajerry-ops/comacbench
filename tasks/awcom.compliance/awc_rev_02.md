# Clause revision impact analysis

Compare the two amendments of the requirement below and respond with ONE
```json code block containing EXACTLY these fields (no extra fields):

{
  "changed_params": {"<param_name>": {"old": number, "new": number}, ...} ({} if none),
  "changed_param_count": integer,
  "added_applicability": sorted list of strings ({} -> []),
  "removed_applicability": sorted list of strings,
  "severity": "major" or "minor",
  "compliance_recheck": boolean
}

Rules: severity = "major" if and only if any parameter value changed OR any
applicability item was added/removed (renumbering/editorial notes alone are
"minor"); compliance_recheck = (severity == "major"). changed_params keys use
the parameter names as printed; old/new are the verbatim numbers.

## Amendment A (2016)

---
ACX-EWIS-302 / Amendment 2016
For the configurations listed, the design shall satisfy: limit load factor 2.1, cabin pressure altitude 8262.3 ft, flap limit speed 186.9 ktas, fuel tank inerting O2 11.2 percent. Applicability: cabin, cargo, engine-mount, landing-gear, wing. Editorial note: this clause was renumbered for readability.
---

## Amendment B (2022)

---
ACX-EWIS-302 / Amendment 2022
For the configurations listed, the design shall satisfy: limit load factor 1.9, cabin pressure altitude 8262.3 ft, flap limit speed 186.9 ktas, fuel tank inerting O2 11.2 percent. Applicability: cabin, cargo, engine-mount, fuselage, landing-gear, wing. Editorial note: this clause was renumbered for readability.
---
