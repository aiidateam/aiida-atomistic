"""
aiida_atomistic

AiiDA plugin which contains data and methods for atomistic simulations
"""

__version__ = "0.1.0a0"

import copy
import functools
import json
import typing as t
import numpy as np

from aiida import orm
from aiida.common.constants import elements

try:
    import ase  # noqa: F401
    from ase import io as ase_io

    has_ase = True
    ASE_ATOMS_TYPE = ase.Atoms
except ImportError:
    has_ase = False

    ASE_ATOMS_TYPE = t.Any

try:
    import pymatgen.core as core  # noqa: F401

    has_pymatgen = True
    PYMATGEN_MOLECULE = core.structure.Molecule
    PYMATGEN_STRUCTURE = core.structure.Structure
except ImportError:
    has_pymatgen = False

    PYMATGEN_MOLECULE = t.Any
    PYMATGEN_STRUCTURE = t.Any

_MASS_THRESHOLD = 1.0e-3
_MAGMOM_THRESHOLD = 1.0e-4
# Threshold to check if the sum is one or not
_SUM_THRESHOLD = 1.0e-6
# Default cell
_DEFAULT_CELL = ((0, 0, 0),) * 3

_valid_symbols = tuple(i["symbol"] for i in elements.values())
_atomic_masses = {el["symbol"]: el["mass"] for el in elements.values()}
_atomic_numbers = {data["symbol"]: num for num, data in elements.items()}

# Default cell
_DEFAULT_CELL = [[0.0, 0.0, 0.0]] * 3
_DEFAULT_PBC = [True, True, True]

_DEFAULT_VALUES = {
    "kind_name": "",
    "mass": 0,
    "charge": 0,
    "magmom": np.array([0, 0, 0]),
    "magnetization": 0,
    "hubbard": None,
    "weight": (1,)
}

_CONVERSION_PLURAL_SINGULAR = {
    "positions": "position",
    "symbols": "symbol",
    "masses": "mass",
    "charges": "charge",
    "magmoms": "magmom",
    "magnetizations": "magnetization",
    "hubbards": "hubbard",
    "weights": "weight",
    "kind_names": "kind_name"

}

_GLOBAL_PROPERTIES = [
    "pbc",
    "cell",
    "custom",
    "hubbard",
    "tot_magmom",
    "tot_charge",
]


_COMPUTED_PROPERTIES = [
    "kinds",
    "cell_volume",
    "dimensionality",
    "formula",
    "is_alloy",
    "has_vacancies",
]
