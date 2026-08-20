# HiLiftAeroML native-volume invalid zero-fill rows

This directory identifies native-volume rows that should be ignored when
using the released volume field data. Every exported flow and statistics field
was verified to be exactly zero on each listed row. This includes stored
pressure, absolute temperature, and density, so the rows do not contain a
physically valid CFD solution state. The all-zero pattern is consistent with
zero-filled placeholder or missing data; the files identify the affected rows
but do not assign a specific cause to the zero fill.

## Files

- `volume_zero_fill_raw_point_ids_all1800.jsonl` lists the case-local raw row
  IDs for all 1,800 cases in human-readable ASCII.
- `volume_zero_fill_raw_point_xyz_all1800.csv` provides the corresponding raw
  native VTU coordinates as a human-readable diagnostic table with columns
  `case_id,raw_point_id,x,y,z`.
- `volume_zero_fill_raw_point_ids_all1800_manifest.json` documents how the rows
  were identified, binds every source archive and both public data files by
  SHA-256, and records integrity checks.
- `SHA256SUMS` contains the publication checksums.

## What the list records

For each case, the listed IDs are zero-based indices in the stored
`PointData` row order of `volume_<case>.vtu`. They identify rows where the raw
stored Float32 `avg(P)` is exactly numeric zero, including either sign of
zero, using no tolerance. The locations were identified before Cp conversion,
normalization, or nondimensionalization and were not derived from model
predictions. This raw-field condition is not equivalent to physical
`Cp == 0`.

The initial `avg(P) == 0.0` test was used to find candidate rows. A subsequent
check verified that all exported fields listed in the manifest are exactly
zero on every candidate row. The published IDs are therefore the rows to
ignore; legitimate physical points are not selected merely because a derived
quantity such as `Cp` is zero.

Across all 1,800 cases there are 419,416,158,837 raw volume rows and 1,232,817
listed zero-fill rows. The list is nonempty for 1,768 cases and empty for 32
cases.

## Reading one case

```python
import json

with open(
    "data_quality/volume_zero_fill_raw_point_ids_all1800.jsonl",
    encoding="ascii",
) as stream:
    for line in stream:
        record = json.loads(line)
        if record["case_id"] == case_id:
            zero_fill_raw_point_ids = record["zero_fill_raw_point_ids"]
            break
    else:
        raise KeyError(case_id)
```

The file has exactly one compact JSON object per line, ordered by
`case_index`; line number is therefore `case_index + 1`. IDs within a case are
sorted and unique. A consumer processing a chunk can use these IDs to locate
and omit the listed rows that fall inside that chunk.

## Coordinate convenience table

The CSV contains one header and exactly 1,232,817 data rows, ordered by
`case_index` and then `raw_point_id`. Its `x`, `y`, and `z` values are copied
from `Points[raw_point_id]` in the native volume VTU without transformation or
unit conversion. The source coordinates are Float32; each value is written
with nine significant decimal digits and verified to round-trip to the exact
stored Float32 value.

Coordinates are descriptive convenience data, not identifiers. Use the pair
`(case_id, raw_point_id)` for exact joins. Do not use coordinate rounding,
nearest-neighbour matching, or a geometric tolerance to redefine row
identity.

## Source provenance

The manifest pins `nvidia/HiLiftAeroML` at immutable revision
`1c266d3869bc2968ff97d2107c9c3919be03ed32`. For every case it records the
repository-relative volume-archive path, byte size, Hugging Face LFS SHA-256,
and extracted VTU member name. The row-ID space is the named VTU obtained by
lossless extraction of that pinned archive.

## Scope

This metadata applies only to the listed native-volume `PointData` rows. It
does not identify or describe any surface rows.

See the repository's root dataset card for licensing and citation details.
