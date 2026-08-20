PROBLEM DESCRIPTION:
Background:
An incomplete Cholesky factorization provides a sparse approximation of the Cholesky factorization for a symmetric positive definite matrix. This factorization is commonly employed as a preconditioner for iterative algorithms such as the conjugate gradient method.

In the Cholesky factorization of a positive definite matrix $A$, we have $A = LL*$, where $L$ is a lower triangular matrix. The incomplete Cholesky factorization yields a sparse lower triangular matrix $K$ that closely approximates $L$. The corresponding preconditioner is $KK*$.

A popular approach to find the matrix $K$ is to adapt the algorithm for the exact Cholesky decomposition, ensuring that $K$ retains the same sparsity pattern as $A$ (any zero entry in $A$ leads to a zero entry in $K$). This method produces an incomplete Cholesky factorization that is as sparse as matrix $A$.

For $i$ from $1$ to $N$ :
$$
L_{i i}=\left(a_{i i}-\sum_{k=1}^{i-1} L_{i k}^2\right)^{\frac{1}{2}}
$$

For $j$ from $i+1$ to $N$ :
$$
L_{j i}=\frac{1}{L_{i i}}\left(a_{j i}-\sum_{k=1}^{i-1} L_{i k} L_{j k}\right)
$$

Create a function to compute the incomplete Cholesky factorization of an input matrix.

PROBLEM STEPS AND FUNCTION HEADERS:
## Step 1
Background:
Background:
An incomplete Cholesky factorization provides a sparse approximation of the Cholesky factorization for a symmetric positive definite matrix. This factorization is commonly employed as a preconditioner for iterative algorithms such as the conjugate gradient method.

In the Cholesky factorization of a positive definite matrix $A$, we have $A = LL*$, where $L$ is a lower triangular matrix. The incomplete Cholesky factorization yields a sparse lower triangular matrix $K$ that closely approximates $L$. The corresponding preconditioner is $KK*$.

A popular approach to find the matrix $K$ is to adapt the algorithm for the exact Cholesky decomposition, ensuring that $K$ retains the same sparsity pattern as $A$ (any zero entry in $A$ leads to a zero entry in $K$). This method produces an incomplete Cholesky factorization that is as sparse as matrix $A$.

For $i$ from $1$ to $N$ :
$$
L_{i i}=\left(a_{i i}-\sum_{k=1}^{i-1} L_{i k}^2\right)^{\frac{1}{2}}
$$

For $j$ from $i+1$ to $N$ :
$$
L_{j i}=\frac{1}{L_{i i}}\left(a_{j i}-\sum_{k=1}^{i-1} L_{i k} L_{j k}\right)
$$

Description:
Create a function to compute the incomplete Cholesky factorization of an input matrix.

Function header:
def ichol(A):
    '''Inputs:
    A : Matrix, 2d array M * M
    Outputs:
    A : Matrix, 2d array M * M
    '''


DEPENDENCIES:
Use only the following dependencies in your solution. Do not include these dependencies at the beginning of your code (they are already imported):
import numpy as np

RESPONSE GUIDELINES:
- Implement ALL step functions in a single ```python block, in the order given.
- Adhere exactly to the provided function headers (names, arguments, docstrings can be kept short).
- Later steps may call functions from earlier steps.
- Do NOT include dependency imports, example usage, or test code.
- Your response should contain ONLY the ```python code block.

