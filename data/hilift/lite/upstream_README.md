---
license: cc-by-4.0
viewer: false
---

# HiLiftAeroML: High-Fidelity Computational Fluid Dynamics Dataset for High-Lift Aircraft Aerodynamics

**Contact:**
Neil Ashton (contact@caemldatasets.org)

## Summary
This dataset provides the first-ever open-source high-fidelity CFD dataset of a high-lift aircraft for the purpose of AI surrogate model development. The dataset is composed of 1,800 samples, arising from 180 geometry variants of the NASA Common Research Model (CRM-HL) across 10 angles of attack (from 4° to 22° in 2° increments). 

One of the key novelties of this dataset is the use of a GPU-accelerated high-fidelity explicit, wall-modeled LES (WMLES) approach on solution-adapted grids containing between 300M and 500M cells. By making this data publicly available, the aim is to accelerate the research and development of AI surrogate modeling within the aerospace industry by addressing the lack of high-fidelity, scale-resolving CFD training data for complex 3D airframes in the high-lift regime.

## CFD Solver
The simulations were performed using the **"Fidelity Charles"** flow-solver, an explicit, unstructured, finite-volume solver for the compressible Navier-Stokes equations. 
* **Accuracy:** 2nd-order accurate in space and 3rd-order accurate in time. 
* **Meshing:** The domain was discretized using "Fidelity Stitch", an unstructured mesh generator based on Voronoi diagrams. 
* **Turbulence Modeling:** To capture complex, unsteady flow phenomena such as massive flow separation, a wall-modeled LES using the Dynamic Smagorinsky subgrid-scale model and an equilibrium wall model were employed.

## How to Cite This Dataset
In order to cite the use of this dataset, please cite the corresponding preprint paper (https://arxiv.org/abs/2605.19565):

```bibtex
@article{ashton2026hiliftaeroml,
  title={{HiLiftAeroML: High-Fidelity Computational Fluid Dynamics Dataset for High-Lift Aircraft Aerodynamics}},
  year={2026},
  journal = {arxiv.org}, url={https://arxiv.org/abs/2605.19565}, 
  author={Ashton, Neil and Clark, Adam and Heidt, Liam and Ivey, Christopher and Bose, Sanjeeb and Agrawal, Rahul and Goc, Konrad and Ranade, Rishi and Adams, Corey and Sharpe, Peter and Nidhan, Sheel and Akkurt, Semit and Leibovici, Daniel and Kossaifi, Jean}
}
```

## Dataset Structure and Files
Each folder (e.g., `geo_LHCi_AoA_j` where `i` is the geometry ID from 001 to 180 and `j` is the angle of attack) corresponds to a different geometry and angle of attack. Inside each run folder, you will find:

* `boundary_geo_LHCi_AoA_j.vtu.tgz`: Time-averaged flow quantities on the surface boundary (approx. 13 GB compressed, 21 GB unzipped).
* `boundary_dual_area_geo_LHCi_AoA_j.npy`: Native-point surface quadrature weights for the corresponding boundary VTU (little-endian float32, one value per VTU point, in exact VTU point order, with units of `in^2`).
* `volume_geo_LHCi_AoA_j.vtu.tgz`: Time-averaged flow quantities within the domain volume (approx. 23 GB compressed, 86 GB unzipped).
* `geo_LHCi_AoA_j.stl`: Surface mesh (tris) of the geometry (approx. 197 MB).
* `geo_LHCi_AoA_j.stp`: Surface geometry definition (approx. 48 MB).
* `force_mom_geo_LHCi_AoA_j.csv`: Time-averaged drag, lift, moment, and pressure/viscous coefficients.
* `geo_values_geo_LHCi_AoA_j.csv`: Reference geometry values used to define the geometry via the DoE method.
* `ref_values_geo_LHCi_AoA_j.csv`: Reference values such as area, Q, and AoA.
* `img_wss_LHCi_AoA_j.png`: Visual rendering of the wall shear stress/skin-friction on the aircraft surface.
* `plot_CD_geo_LHCi_AoA_j.png`: Convergence plot of the Drag Coefficient over time.
* `plot_CL_geo_LHCi_AoA_j.png`: Convergence plot of the Lift Coefficient over time.
* `plot_CM_geo_LHCi_AoA_j.png`: Convergence plot of the Pitching Moment Coefficient over time.

In addition to the files per run folder, there are also general summary files in the root directory:
* `geo_values_all.csv`: Reference geometry values used to define the geometry via the DoE method for all runs.
* `force_mom_all.csv`: Time-averaged drag, lift, moment, and pressure/viscous coefficients for all runs.
* [`splits/`](splits/): Deterministic train/validation/test split manifest, documentation, and generation code.
* [`surface_dual_areas/`](surface_dual_areas/): Definition, generator, complete 1,800-case manifest, per-case topology/provenance records, validation summaries, and SHA-256 hashes for the native-point surface quadrature sidecars.
* [`data_quality/`](data_quality/): Native-volume row IDs and raw XYZ coordinates for invalid zero-filled rows that should be ignored, with provenance and SHA-256 checksums.

## Recommended Dataset Splits

For reproducible machine-learning evaluation, HiLiftAeroML provides 14 deterministic split families in [`splits/manifest.json`](splits/manifest.json). Case IDs match the top-level `geo_LHC..._AoA_...` directories.

| Evaluation goal | Suggested splits | Training population |
|---|---|---:|
| Standard baseline and case-level data efficiency | `full` → `medium` → `scarce` → `super_scarce` | 1260 → 510 → 210 → 35 cases |
| Unseen-geometry generalization and data efficiency | `geometry` → `geometry_medium` → `geometry_scarce` → `geometry_super_scarce` | 126 → 51 → 21 → 4 complete geometries |
| Fixed-AoA unseen-geometry evaluation | `single_aoa_4`, `single_aoa_12`, `single_aoa_22` | 126 train / 18 validation / 36 test geometries |
| Out-of-distribution evaluation | `aoa`, `deflection`, `stall` | High-AoA, high-deflection, or post-stall extrapolation |

The levels within each data-efficiency ladder are nested and share the same validation and test sets, enabling direct comparisons across training-set sizes. Use validation data for model selection and reserve test data for final evaluation. See [`splits/README.md`](splits/README.md) for the complete definitions, counts, and selection guidance, or [`splits/generate_splits.py`](splits/generate_splits.py) for the generation and validation logic.

## Area-Weighted Evaluation on the Native Surface

Every raw boundary VTU now has a matching `boundary_dual_area_<case>.npy` sidecar. If a native surface polygon is fan-triangulated, each triangle contributes one third of its area to each incident vertex. The resulting mass-lumped dual areas sum to the fan-triangulated surface area and allow point-data predictions to be scored by physical surface measure rather than by the nonuniform density of mesh points.

The sidecar applies **only** to the corresponding raw `boundary_<case>.vtu`: its length equals `mesh.n_points`, and entry `i` weights point-data entry `i`. Do not use it after reordering, resampling, converting to STL, or processing the mesh into another representation. Accumulate statistics in float64 even though the stored weights are float32. For a scalar or vector field, an area-weighted relative L2 error can be computed as follows:

```python
import numpy as np
import pyvista as pv

case = "geo_LHC001_AoA_4"
mesh = pv.read(f"{case}/boundary_{case}.vtu")
w = np.load(
    f"{case}/boundary_dual_area_{case}.npy", mmap_mode="r"
)
assert w.dtype == np.dtype("<f4") and w.shape == (mesh.n_points,)

# pred and reference have shape (mesh.n_points,) for a scalar field or
# (mesh.n_points, n_components) for a vector field.
err2 = np.square(pred.astype(np.float64) - reference.astype(np.float64))
ref2 = np.square(reference.astype(np.float64))
if err2.ndim == 2:
    err2 = err2.sum(axis=1)
    ref2 = ref2.sum(axis=1)

numerator = np.sum(w * err2, dtype=np.float64)
denominator = np.sum(w * ref2, dtype=np.float64)
relative_l2 = np.sqrt(numerator / denominator)
```

The weights are in square inches because the native coordinates are in inches. A constant unit conversion cancels from normalized metrics such as relative L2 and weighted means. See [`surface_dual_areas/README.md`](surface_dual_areas/README.md) and [`surface_dual_areas/manifest.json`](surface_dual_areas/manifest.json) for the exact algorithm and validation contract.

## How to Download

HiLiftAeroML is publicly available on Hugging Face. There is no Hugging Face access charge, but the dataset is very large: the full repository is about 66.9 TB as stored on Hugging Face and substantially larger after extracting the `.tgz` archives. Please make sure you have sufficient storage and bandwidth before downloading large subsets.

We recommend using the Hugging Face CLI rather than `git clone` for selective downloads, resumable local downloads, dry-run previews, and Xet-backed large-file support.

### Prerequisites

```bash
pip install -U huggingface_hub hf_xet
```

Authentication is optional for this public dataset, but strongly recommended for large downloads to avoid unauthenticated rate limits:

```bash
hf auth login
```

### Example 1: Preview or Download the Full Dataset

Preview the full download first:

```bash
hf download nvidia/HiLiftAeroML \
  --repo-type dataset \
  --local-dir ./hiliftaeroml_data \
  --dry-run
```

Remove `--dry-run` to download the full dataset:

```bash
hf download nvidia/HiLiftAeroML \
  --repo-type dataset \
  --local-dir ./hiliftaeroml_data
```

### Example 2: Download Selected CSV Metadata and Split Files

The following command downloads only force/moment CSVs, geometry CSVs, reference CSVs, and split files. Keep the glob patterns in quotes so your shell does not expand them locally.

Preview first:

```bash
hf download nvidia/HiLiftAeroML \
  --repo-type dataset \
  --local-dir ./hiliftaeroml_data \
  --include "geo_LHC*_AoA_*/force_mom_*.csv" \
  --include "geo_LHC*_AoA_*/geo_values_*.csv" \
  --include "geo_LHC*_AoA_*/ref_values_*.csv" \
  --include "force_mom_all.csv" \
  --include "geo_values_all.csv" \
  --include "splits/**" \
  --dry-run
```

Remove `--dry-run` to download those files.

### Example 3: Download Only the Surface Quadrature Sidecars

The following command downloads the 1,800 native-point NPY files and their algorithm, provenance, and validation metadata without downloading the CFD archives. The sidecars occupy about 1.02 TB (946.7 GiB) in total, so preview the selection first.

```bash
hf download nvidia/HiLiftAeroML \
  --repo-type dataset \
  --local-dir ./hiliftaeroml_data \
  --include "geo_LHC*_AoA_*/boundary_dual_area_*.npy" \
  --include "surface_dual_areas/**" \
  --dry-run
```

Remove `--dry-run` to download those files.

### Example 4: Download Specific Runs with a Bash Script

This script loops over geometry IDs 1-180 and AoA values 4-22 in steps of 2. By default it runs in preview mode. Set `DRY_RUN=0` to download the files.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

REPO="nvidia/HiLiftAeroML"
LOCAL_DIR="./hiliftaeroml_data"
DRY_RUN="${DRY_RUN:-1}"

HF_ARGS=()
if [[ "$DRY_RUN" == "1" ]]; then
  HF_ARGS+=(--dry-run)
fi

for i in {1..180}; do
  XX=$(printf "%03d" "$i")

  for YY in $(seq 4 2 22); do
    ID="geo_LHC${XX}_AoA_${YY}"
    echo "Processing: $ID"

    FILES=(
      "$ID/boundary_${ID}.vtu.tgz"
      "$ID/${ID}.stl"
      "$ID/${ID}.stp"
      "$ID/force_mom_${ID}.csv"
      "$ID/geo_values_${ID}.csv"
      "$ID/ref_values_${ID}.csv"
      "$ID/volume_${ID}.vtu.tgz"
    )

    hf download "$REPO" "${FILES[@]}" \
      --repo-type dataset \
      --local-dir "$LOCAL_DIR" \
      "${HF_ARGS[@]}"
  done
done
```

To actually download after previewing:

```bash
DRY_RUN=0 bash download_hiliftaeroml.sh
```

## Credits
The dataset was created through a collaboration between **NVIDIA**, **Cadence Design Systems**, and **The Boeing Company**. 

Computing resources were generously provided by:
* Cadence
* NVIDIA
* Texas Advanced Computing Center (TACC) at The University of Texas at Austin
* Swiss National Supercomputing Centre (CSCS)
* Oak Ridge Leadership Computing Facility (ORNL)

## License
This dataset is provided under the permissive open-source **CC-BY-4.0** license. Users are free to share and adapt the material for any purpose, even commercially, provided appropriate credit is given to the original authors.

## Version History

* 07/08/2026 - added native-boundary-point dual-area NPY sidecars for all 1,800 cases, together with a complete manifest, hashes, validation records, and generation code for reproducible area-weighted surface evaluation

* 06/07/2026 - updated the splits to include a couple of extra ones (geometry_medium, scarce, super_scare and medium)

* 26/05/2026 - IDs 0-43 for angles 16-22 had incomplete force_mom (didn't have std dev etc). Corrected. Please download forces again if you took files before this date

* 20/05/2026 - dataset fully uploaded and arxiv preprint made available
