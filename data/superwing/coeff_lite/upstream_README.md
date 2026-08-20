---
license: cc-by-sa-4.0
---
**SuperWing**, a comprehensive benchmark dataset of transonic swept wings comprising 4239 wing shapes and nearly 30,000 flow fields across diverse geometries and
operating conditions. Unlike previous efforts that rely on perturbations of a baseline wing, SuperWing is generated using a simplified yet expressive 
parameterization scheme. By incorporating spanwise-varying dihedral, twist, and airfoil characteristics, the dataset captures realistic design complexity and 
ensures greater diversity than existing ones. Please refer to our [arXiv paper](https://arxiv.org/abs/2512.14397) for more details on the dataset. 

![{AB7AE610-885E-4D76-8658-C797ACFC1D02}](https://cdn-uploads.huggingface.co/production/uploads/6878e482bd4380c813fd99de/xUllU2wTB0GEyuS1OmKjd.png)

The simulations are conducted on the 160-core high-performance computing cluster at AeroLab, Tsinghua University

# Features

1. Focusing on the **"kink" wings** (with two segments instead of one in the spanwise direction) under transonic regime (Mach number between 0.75 and 0.90), which bring more complex flow features and are closer to the industry.
2. **More diversity** on the wing shape by generating them from basic parameters instead of perturbing from a baseline wing shape
3. RANS simulation with **well-validated** solver `ADflow` and structural computational mesh.

---

# Data overview

## Files

(N=28856, Nshape=4239)

| Type | File | Description | Shape | Size |
|---|---|---|---|---|
| Metadata | `config.dat` | shape parameters | \\(N_{\mathrm{shape}} \times 56\\) | 5.0 MB |
|  | `index.npy` | indexing, operating conditions, and aerodynamic coefficients | \\(N_{\mathrm{sample}} \times 12\\) | 2.8 MB |
|  | `training_samples_index.txt` | training sample split | -- | 0.1 MB |
| Shape / Surface flow | `data_surf.npy.zst` | surface simulation mesh and flow quantities on mesh points (cell center) | \\(N_{\mathrm{sample}} \times 10 \times 44{,}096\\) | 26.7 GB (85.3 GB) |
|  | `origingeom.npy` | [STRUCTURED] reference surface mesh (grid points) | \\(N_{\mathrm{shape}} \times 3 \times 129 \times 257\\) | 3.3 GB |
|  | `geom0.npy` | [STRUCTURED] reference surface mesh (cell center) | \\(N_{\mathrm{shape}} \times 3 \times 128 \times 256\\) | 3.3 GB |
|  | `data.npy` | [STRUCTURED] surface flow quantities at reference mesh (cell center) | \\(N_{\mathrm{sample}} \times 3 \times 128 \times 256\\) | 22.7 GB |
| Volumetric flow | `data_vol.xx.npy.zst` | coordinates and flow quantities at near-field volumetric simulation mesh (cell center) | \\(N_{\mathrm{sample}} \times 8 \times 3{,}086{,}720\\) | 3.2 TB (5.3 TB) |

## Channels (for geometry and flow)

| Index | `data_surf.npy` | `data_vol.npy` | Index | `origingeom.npy`, `geom0.npy` |
|---|---|---|---|---|
| 0 | Coordinate \\(x\\) | Coordinate \\(x\\) | 0 | Coordinate \\(x\\) |
| 1 | Coordinate \\(y\\) | Coordinate \\(y\\) | 1 | Coordinate \\(y\\) |
| 2 | Coordinate \\(z\\) | Coordinate \\(z\\) | 2 | Coordinate \\(z\\) |
| 3 | Density \\(\tilde \rho\\) | Density \\(\tilde \rho\\) |  | `data.npy` |
| 4 | Pressure coef. \\(C_{p}\\) | Pressure \\(\tilde p\\) | 0 | Pressure coef. \\(C_{p,\mathrm{scaled}}\\) |
| 5 | \\(x\\) skin friction coef. \\(C_{f,x}\\) | \\(x\\) velocity \\(\tilde V_x\\) | 1 | Streamwise skin friction coef. \\(C_{f,\tau,\mathrm{scaled}}\\) |
| 6 | \\(y\\) skin friction coef. \\(C_{f,y}\\) | \\(y\\) velocity \\(\tilde V_y\\) | 2 | \\(z\\) skin friction coef. \\(C_{f,z,\mathrm{scaled}}\\) |
| 7 | \\(z\\) skin friction coef. \\(C_{f,z}\\) | \\(z\\) velocity \\(\tilde V_z\\) |  |  |
| 8 | Temperature \\(\tilde T\\) |  |  |  |

- \\(\tilde{(\cdot)}\\) means the relative value to the freestream condition ( \\(\rho_\infty, p_\infty, T_\infty, V_\infty\\) )
- \\((\cdot)_{\mathrm{scaled}}\\) means they are scaled to have a similar magnitude. The scaling factor for the three channels are 1, 150, 300.

**Coefficients definition**

- Pressure coefficient: \\(C_p = \frac{p-p_\infty}{0.5\rho_\infty V_\infty^2}\\)
- Friction coefficient: (vector) \\(C_{\bm f} = [C_{f,x}, C_{f,y}, C_{f,z}]^T = \frac{\bm{\tau_w}}{0.5\rho_\infty V_\infty^2}, \quad \bm{\tau_w}=\mu \frac{\partial \bm {u_t}}{\partial s_n}\\)
  -  \\(C_{f,\tau,\mathrm{scaled}}\\) means the component in the \\(x\\) - \\(y\\) surface.

---

# Data format

## Meta Data

The metadata include the wing geometry parameters, operating conditions, aerodynamic coefficients, group identifiers, and predefined train/test splits used in this work.

### `configs.dat`

`configs.dat` stores the parametric definition of each wing geometry and can be used to reconstruct the geometry from scratch. It contains:

- **Columns 1–7:** Global planform parameters, including:
  - sweep angle \\(\Lambda_\mathrm{LE}\\)
  - tip/kink dihedral angles \\(\Gamma_\mathrm{LE,tip}\\), \\(\Gamma_\mathrm{LE,kink}\\)
  - aspect ratio \\(AR\\)
  - taper ratio \\(TR\\)
  - kink location \\(\eta_k\\)
  - root parameter \\(\kappa_\mathrm{root}\\)

- **Columns 8–17:** Spanwise variation parameters:
  - thickness ratios \\(r_t\\) ( \\(\times 3\\))
  - deformation parameters \\(r_\delta\\) ( \\(\times 4\\))
  - twist angles \\(\alpha_\mathrm{tw}\\) ( \\(\times 4\\))

- **Columns 18–38:** Baseline airfoil shape:
  - CST coefficients for upper surface ( \\(\times 10\\))
  - CST coefficients for lower surface ( \\(\times 10\\))

- **Columns 39–56:** Operating conditions:
  - eight pairs of Mach number \\(Ma\\) and angle of attack \\(\alpha\\)

> Some operating conditions may be missing in the final dataset if CFD simulations fail to converge.


### `index.npy`

`index.npy` provides metadata for each flow-field sample. Each row corresponds to one sample. It includes:

- **Geometry mapping**
  - Column 1: geometry index (linked to `configs.dat`)
  - Column 2: operating-condition index within the geometry

- **Operating conditions**
  - Column 3: angle of attack \\(\alpha\\)
  - Column 4: Mach number \\(Ma\\)

- **Reference quantities**
  - Column 5: half reference area \\(S_{1/2}\\)
  - Column 6: half span \\(b_{1/2}\\)

- **Aerodynamic coefficients**
  - lift coefficient \\(C_L\\)
  - drag coefficient \\(C_D\\)
  - pitching moment coefficient \\(C_{M,z}\\)

  > These coefficients are computed from pressure coefficient and skin-friction vector by surface integration:
  >
  > \\(
  > C_{\bm F}=[C_x,C_y,C_z]^T =\frac{1}{S_{1/2}} \sum_{i=1}^{N_{\mathrm{cell}}} \left[ C_p^{(i)}\bm n^{(i)} + \left(C_{\bm f}^{(i)} - (C_{\bm f}^{(i)}\cdot \bm n^{(i)})\bm n^{(i)} \right) \right] A^{(i)}
  > \\)
  > 
  > Lift and drag are obtained by rotating the force vector according to the angle of attack:
  > 
  > \\(
  > [C_L,C_D,C_z]^T=\bm R_\alpha C_{\bm F}
  > \\)
  >
  > The pitching moment coefficient is:
  > 
  > \\(
  > C_{M,z}=\frac{1}{S_{1/2}c_\mathrm{ref}}\sum_{i=1}^{N_{\mathrm{cell}}}\bm r^{(i)}\times\left(\left[C_p^{(i)}\bm n^{(i)}+\left(C_{\bm f}^{(i)}-(C_{\bm f}^{(i)}\cdot\bm n^{(i)})\bm n^{(i)}\right)\right]A^{(i)}\right)
  > \\)
  >
  > where: \\(\bm n^{(i)}\\): outward normal vector, \\(A^{(i)}\\): surface-cell area, \\(\bm r^{(i)}\\): position vector from the reference point, \\(c_\mathrm{ref}=1.0\\): reference chord length

  Two sets of aerodynamic coefficients are provided:

  - **Columns 7–9:** coefficients computed on the original CFD mesh using `ADflow`
  - **Columns 10–12:** coefficients evaluated on the structured reference mesh for machine-learning applications

### `training_samples_index.txt`

`training_samples_index.txt` stores the indices of training samples used in technical validation.

The dataset is split by wing shape to evaluate generalization:

- 90% of wing shapes are randomly selected for training
- the remaining shapes are used for testing

Training sample indices are recorded in this file.

### Parquet Files

`train.parquet` and `test.parquet` provide metadata organized into training and test splits for convenient visualization and loading in HuggingFace.

---

## Surface shape and flow

### Original data [NEW]

`data_surf/data_surf.npy.zst` provides the centric coordinates of the exact surface mesh for the simulations, and the surface flow values on the surface mesh centers.
To enable compact storage, we flatten the original multi-block structured mesh into a one-dimensional sequence of 44,096 points.

<img src="https://cdn-uploads.huggingface.co/production/uploads/6878e482bd4380c813fd99de/VSgQ1Op01mIa-g_4f4K3J.png" alt="surface" width="40%">

### Structured surface shape and flow

`origingeom.npy`, `geom0.npy`, `data.npy`

> Besides the raw multi-block solver output, we also prepare the surface mesh and flow fields in a format suitable for ML models with structured inputs and outputs.


The reference mesh `geom0` contains the cell-centric coordinates of the reference surface mesh with size \\( 256 \times 128 \times 3 \\), and the three channels stand
for \\( x, y, z \\). The surface physical quantities `data.npy` are on the same reference mesh with size \\( 256 \times 128 \times 3 \\), and the three channels stand for
\\( C_p, C_{f,\tau}, C_{f,z} \\).   (the latter two are the decomposed friction coefficients on the streamwise and spanwise directions). 

**reference mesh**: The simulation mesh on the wing surface is first interpolated to a reference mesh. In the spanwise ($j$-direction), 128 cross-sectional planes are
sampled with even spacing, and tips are excluded. For each cross-section (i-direction), a fixed set of normalized chordwise positions \\( \{(x/c)_i\} \\) s is used for both 
the upper and lower surfaces, and the tail edge is represented only with one cell. The reference mesh along the wing surface is then unfolded as shown below, resulting 
in a final vertex surface grid of \\( 257 \times 129 \\) points per wing (`origingeom.npy`). This is useful when we need to calculate coefficients from the surface flow outputs.
The cell-centric grid for the mesh is obtained just by averaging the coordinates at the four vertices.

<img src="https://cdn-uploads.huggingface.co/production/uploads/6878e482bd4380c813fd99de/deWUNg0C2bxl7ZDQFfowu.png" alt="transform" width="40%">

---

## Volumetric flow quantities on the near-field simulation mesh

`data\_vol/data\_vol.xx.npy.zst` provides the volumetric flow, including the cell-centric coordinates and five core flow quantities at each simulation cell. They are again 
defined as the relative value to the freestream. Similar to the surface data, we flatten and concatenate the multi-block mesh into a one-dimensional point cloud sequence. 

Given that it requires a large far field, the flow variables at far-field mesh points show only negligible deviations from the freestream values. To avoid this redundancy, 
we include the first 71 layers of mesh in the wall-normal dimension for each block. This produces 3,086,720 points per volumetric flow field.


<img src="https://cdn-uploads.huggingface.co/production/uploads/6878e482bd4380c813fd99de/Pjwd0YVNeySsr6ycsJHRN.png" alt="vol" width="30%">

---

# Postprocess

## Aerodynamic coefficients

One can integrate surface flow (formatted as in `data.npy`) to get the aerodynamic coefficients (i.e., the lift coefficient $C_L$, the drag coefficient $C_D$, the pitching 
moment coefficient $C_{M,z}$) with the code in `floGen` (`flogen.post`). We also provide the `post.py` file here for simple download. 

Remark. 
1. It uses `pytorch`.
2. The geometric information should be with the grid point mesh (`origingeom.npy`), not the cell-centric mesh (`geom0.npy`).
3. The values in `data.npy` are already non-dimensionalized with the freestream condition

```python
import post
geom = torch.from_numpy(np.load('origingeom.npy'))[i_shape]).float().to(device)
aoa = 3.0
ref_area = np.load('index.npy')[i_sample, 4]

output = <your_model_output> # with shape (H, W, 3)

cf_xyz = post._get_xz_cf_t(geom, output[..., 1:]) # transfer to xyz coordinates

force_coefficients = post.get_force_2d_t(geom=geom, aoa=aoa, cp=output[..., 0], cf=cf_xyz) / ref_area  # returns: CD, CL, CZ
moment_coefficients = post.get_moment_2d_t(geom=geom, cp=output[..., 0], cf=cf_xyz, ref_point=[0.25, 0, 0]) / ref_area   # returns: CMx, CMy, CMz
```
One can also use the `cfdpost` repo (https://github.com/YangYunjia/cfdpost).

```python
from cfdpost.wing.basic import BasicWing

geom = torch.from_numpy(np.load('origingeom.npy'))[i_shape]).float().to(device)
geom_infos = {}
geom_infos['ref_area'] = np.load('index.npy')[i_sample, 4]
aoa = 3.0

output = <your_model_output> # with shape (H, W, 3)

wg1 = BasicWing(paras=geom_infos, aoa=aoa, iscentric=True)
wg1.read_formatted_surface(geometry=geom, data=output, isinitg=False, isnormed=False)
wg1.aero_force()
cl_real = wg1.coefficients # CL, CD, CMz
```

## Visualization

To visualize the wing surface field, we provide a brief code that gives a not bad looking.

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

def color_map(data, c_map, alpha, dmin=None, dmax=None):
    dmin = np.nanmin(data) if dmin is None else dmin
    dmax = np.nanmax(data) if dmax is None else dmax
    _c_map = mpl.colormaps.get_cmap(c_map)

    norm = mpl.colors.Normalize(vmin=dmin, vmax=dmax)
    _sm = mpl.cm.ScalarMappable(norm=norm, cmap=_c_map)
    _colors = _sm.to_rgba(data)
    _colors[..., -1] = alpha
    
    return _colors, _sm

geom = np.load('data/ppn2norigingeom.npy')[0]
output = <your_model_output> # with shape (H, W, 3)

fig = plt.figure(figsize=(10, 4), dpi=200)
ax = fig.add_subplot(projection='3d')

elev = 68; azim =120 

colors, sm = color_map(output[..., 0], 'gist_rainbow', alpha=1, dmin=-1, dmax=1)    # cp
ax.plot_surface(*geom[[0,2,1]], facecolors=colors, edgecolor='none', rstride=1, cstride=3, shade=True)
ax.view_init(elev=elev, azim=azim)
ax.set_axis_off()
ax.grid(False)
ax.xaxis.pane.set_visible(False)
ax.yaxis.pane.set_visible(False)
ax.zaxis.pane.set_visible(False)

plt.show()
```

This should gives sth. like:

<img src="https://cdn-uploads.huggingface.co/production/uploads/6878e482bd4380c813fd99de/8_e3e0Qjik3TSv4evI7dR.png" alt="transform" width="30%">

