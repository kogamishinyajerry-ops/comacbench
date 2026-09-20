# Trusted resume v1 — B02 / B04

Scope authorized on 2026-09-05: protect all five runner CLIs from incompatible cached
results and make hidden execution manifests replay the selected hidden task set.
B03 spreadsheet grading is a separate change and does not alter this protocol.

- Keep existing CLI options and result score semantics.
- Add versioned identity metadata within the existing extensible manifest `extra`
  and result `artifacts` objects; old reports/readers continue to work.
- Identify the adapter, registry, actual model/provider settings (never credentials),
  seed, selected task specs and effective prompts, assets, environment, and Harness
  options. Hash declared gold/QoI files and oracle companion contents as well.
  Persist hashes for task/prompt contents, never hidden answers/prompts.
- Validate every cached result before any provider invocation or manifest rewrite.
  A missing legacy identity, identity mismatch, malformed result, or extra task file
  refuses resume with an actionable new-output-directory message. Do not rewrite
  history to assign identities retrospectively.
- Write the manifest before the first task, so interruption leaves a resumable run.
  Publish JSON atomically. Permit one writer per output directory; release its lock
  on normal exit, exceptions, and process death.
- A nonempty run requires `--resume`; this prevents accidental overwrites when a
  caller forgets the flag. `--resume` on an empty output directory still starts a run.
- `n_tasks` counts the selected execution set, including hidden/limit/partial-oracle
  selection. Record selected IDs. Replay commands quote paths, use the running
  interpreter, carry hidden/seed/limit/iterate/scaffold/partial-oracle options, and
  include `--resume` for safe replay into the same directory. For a fresh rerun,
  change `--out` to a new directory.
- This is local consistency checking, not cryptographic authenticity or stronger
  sandboxing. External solver/dependency environment certification is outside this fix.
  The writer lock uses POSIX flock (the existing macOS/Linux execution environments).

Validation seam: actual Python runner CLI -> result JSON + manifest + exit status.
Use temporary, fictional fixtures and oracle/stub or a local fake provider endpoint.
No production provider requests or changes to historical results are needed.
