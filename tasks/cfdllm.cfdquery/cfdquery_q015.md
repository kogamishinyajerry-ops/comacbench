In a reacting flow solver on curved high-order DG elements, the domain has multiple hp-interface transitions and contains a flame front advancing into a low-Mach post-shock layer. The source term is \( \omega_i = A_i Y_i^2 \exp(-E_i/(T+\sin(x))) \), Jacobian \( J \in \mathbb{P}^{p-1} \), while \( Y_i, T \in \mathbb{P}^p \). No entropy variable projection is applied. Severe entropy drift is observed localized near p-discontinuities and curvature peaks. What mechanism most likely produces the dominant irreversible entropy production?

1. Modal inconsistency between \( \omega_i \in \mathbb{P}^{3p} \) and \( \ln Y_i \in \mathbb{P}^{2p} \) leads to residual terms \( W_i \omega_i \in \mathbb{P}^{5p} \), causing high-frequency aliasing with curvature amplification via \( J \cdot \sin(x) \)
2. Quadrature on curved elements loses accuracy for \( \sin(x) \) under the geometric mapping, leading to global entropy error even with exact flux and projection
3. Exponential source stiffness dominates entropy response, and without time splitting, entropy growth is due to RK temporal aliasing under stiff dynamics
4. Split-form structure lacks entropy correction terms for non-conservative curvature-driven source coupling, leading to oscillatory divergence

Answer with only the number (1, 2, 3, or 4).
