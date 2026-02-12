"""Constants used throughout the structure module."""

import numpy as np
from aiida.common.constants import elements

_MASS_THRESHOLD = 1.0e-3
_MAGMOM_THRESHOLD = 1.0e-4
# Threshold to check if the sum is one or not
_SUM_THRESHOLD = 1.0e-6

_valid_symbols = tuple(i["symbol"] for i in elements.values())
_atomic_masses = {el["symbol"]: el["mass"] for el in elements.values()}
_atomic_numbers = {data["symbol"]: num for num, data in elements.items()}
