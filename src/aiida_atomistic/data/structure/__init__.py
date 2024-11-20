"""
aiida_atomistic

AiiDA plugin which contains data and methods for atomistic simulations
"""

__version__ = "0.1.0a0"

_MASS_THRESHOLD = 1.0e-3
# Threshold to check if the sum is one or not
_SUM_THRESHOLD = 1.0e-6
# Default cell
_DEFAULT_CELL = [[0.0, 0.0, 0.0]] * 3
_DEFAULT_PBC = [True, True, True]

_DEFAULT_VALUES = {
    "masses": 0,
    "charges": 0,
    "magmoms": [0, 0, 0],
    "hubbard": None,
    "weights": (1,)
}
