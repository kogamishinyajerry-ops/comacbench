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
ACX-LANDING-305 / Amendment 2016
For the configurations listed, the design shall satisfy: limit load factor 2.8, cabin pressure altitude 6285.0 ft, flap limit speed 172.1 ktas, fuel tank inerting O2 9.8 percent. Applicability: cargo, engine-mount, flight-deck, fuselage, landing-gear. Editorial note: this clause was renumbered for readability.
---

## Amendment B (2022)

---
ACX-LANDING-305 / Amendment 2022
For the configurations listed, the design shall satisfy: limit load factor 2.6, cabin pressure altitude 6285.0 ft, flap limit speed 172.1 ktas, fuel tank inerting O2 10.1 percent. Applicability: cargo, engine-mount, flight-deck, landing-gear. Editorial note: this clause was renumbered for readability.
---
