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
"minor"); compliance_recheck = (severity == "major"). In changed_params, use
ONLY the canonical JSON keys below for parameters whose numeric values changed;
old/new are the verbatim numbers (no unit conversion). Omit unchanged parameters.

| Parameter wording in the amendments | Canonical JSON key |
| --- | --- |
| limit load factor | `limit_load_factor` |
| cabin pressure altitude (ft) | `cabin_pressure_altitude_ft` |
| flap limit speed (ktas) | `flap_limit_speed_ktas` |
| fuel tank inerting O2 (percent) | `fuel_tank_inerting_o2_pct` |

## Amendment A (2016)

---
ACX-STALL-301 / Amendment 2016
For the configurations listed, the design shall satisfy: limit load factor 2.4, cabin pressure altitude 9479.6 ft, flap limit speed 199.3 ktas, fuel tank inerting O2 10.0 percent. Applicability: empennage, engine-mount, landing-gear, wing. Editorial note: this clause was renumbered for readability.
---

## Amendment B (2022)

---
ACX-STALL-301 / Amendment 2022
For the configurations listed, the design shall satisfy: limit load factor 2.4, cabin pressure altitude 9479.6 ft, flap limit speed 189.3 ktas, fuel tank inerting O2 10.0 percent. Applicability: engine-mount, landing-gear, wing. Editorial note: this clause was renumbered for readability.
---
