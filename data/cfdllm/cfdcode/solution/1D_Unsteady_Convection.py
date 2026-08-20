import numpy as np
import A03_solver as s
import matplotlib.pyplot as plt

# Input parameters
L = 2.0 # m, length
BCa = 0.0 # lHS BC
BCb = 0.0 # RHS BC
u = 0.2 # m/s, velocity
N = 800
Ts = 0.25*L/u


# Numerical solution using Explicit UDS

xsch = 'CDS'
tsch = 'explicit'
alpha = 0.5
xcv, phi_0, phi_ECp5,alphap5 = s.solve_phi_array(L,N,Ts,alpha,u,BCa,BCb,xsch,tsch)

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
np.save(output_file, phi_ECp5)
