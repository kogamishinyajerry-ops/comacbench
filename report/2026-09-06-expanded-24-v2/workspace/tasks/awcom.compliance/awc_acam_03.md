# Compliance method selection (ACAM) — ACX-FUEL-243

Read the requirement card and the available evidence, then respond with ONE
```json code block containing EXACTLY these fields (no extra fields):

{
  "clause_id": string,
  "primary_method": "MC<n>",
  "secondary_methods": sorted list of "MC<n>" strings (ascending),
  "witnesses_required": boolean,
  "documented_only": boolean
}

Compliance method catalog (authoritative for this task; ACX fictional standard):
- MC0 = compliance statement (符合性声明)
- MC1 = descriptive documentation / drawings (说明性文件)
- MC2 = analysis / calculation (分析计算)
- MC3 = safety assessment (安全性评估)
- MC4 = laboratory test (试验室试验)
- MC5 = ground test on the aircraft (地面试验)
- MC6 = flight test (试飞验证)
- MC7 = aircraft inspection (航空器检查)
- MC8 = simulator test (模拟器试验)
- MC9 = equipment qualification (设备合格性)

Selection rules (apply exactly):
1. Each available evidence item maps to exactly one method as stated on the card.
2. primary_method = the available method with the HIGHEST precedence, where
   precedence (high to low) is:
   MC6 > MC5 > MC4 > MC8 > MC9 > MC3 > MC2 > MC7 > MC1 > MC0.
3. secondary_methods = all OTHER available methods, sorted by method code ascending.
4. witnesses_required = true if and only if primary_method is MC6 (flight test
   requires certification witnesses).
5. documented_only = true if and only if every available method is MC0 or MC1.

## Requirement card

---
Document: ACX-FUEL-243
Section: §5.23 — FUEL category certification requirement
The design shall demonstrate compliance for this clause using the evidence
listed below. Available evidence:
1. a descriptive drawing set is complete -> MC1
2. a full-flight simulator session is available -> MC8
3. the equipment holds a qualification certificate -> MC9
---
