Consider the Laplace equation describing steady state heat conduction in a two dimensional rectangular domain. If the equation is discretized using finite difference approximations with uniform grid spacing in both directions, and if the resulting equations are properly arranged and written in the form of a matrix equation, then the non-zero coefficients in the coefficient matrix will (assume array of unknowns is a 1D array obtained by column major ordering of the 2D unknowns)

1. have a tridiagonal structure with three adjacent diagonals including the main diagonal.
2. have a pentadiagonal structure with five adjacent diagonals including the main diagonal.
3. have a pentadiagonal structure with three adjacent diagonals and two other diagonals separated by diagonals containing zeroes.
4. be the sum of two tridiagonal matrices each containing three adjacent diagonals.

Answer with only the number (1, 2, 3, or 4).
