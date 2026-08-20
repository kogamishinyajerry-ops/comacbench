"""
Solution file for 1d, unsteady, convection-diffusion solver
"""

import numpy as np
import A04_solver as slv
import matplotlib.pyplot as plt

# Input parameters
L = 2.0  # m, length
BCa = 0.0  # lHS BC
BCb = 0.0  # RHS BC
u = 0.2  # m/s, velocity
rho = 1.0  # kg/m^3, density
gamma = 0.001  # kg/m/s, diffusive coefficient
N = 800
Tfinal = L / u
alpha = 1.0

fig = plt.figure(1, figsize=(6, 4))

times = [0.25 * Tfinal, 0.5 * Tfinal, 0.75 * Tfinal, Tfinal]
# times = [0.5*Tfinal,Tfinal]

# clr = ['c','m','b','g']
phi = None
for tf in times:
    xcv, phi_0, phi_f = slv.solve_phi_array(L, N, tf, alpha, u, rho, gamma)
    if tf == 2.5:
        phi = phi_f
    plt.plot(xcv, phi_f, label='t = %1.1f s' % tf)

plt.plot(xcv, phi_0, 'k', label='t = 0.0 s')
plt.xlabel("Length [m]", fontsize=14)
plt.ylabel(r'$\phi$', fontsize=14)
plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
plt.title('FVM Approximated Unsteady Convective-Diffusive Flow')
# plt.ylim(-0.05, 1.5)
plt.tight_layout()
# plt.show()

##########################################################################
import os

# === Paths ===
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # PDE_Benchmark root
OUTPUT_FOLDER = os.path.join(ROOT_DIR, "results")

# Ensure the output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# Get the current Python file name without extension
python_filename = os.path.splitext(os.path.basename(__file__))[0]

# Define the file name dynamically
output_file = os.path.join(OUTPUT_FOLDER, f"phi_{python_filename}.npy")

# Save the array u in the results folder
np.save(output_file, phi)
