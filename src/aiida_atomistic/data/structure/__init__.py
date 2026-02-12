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

# Import constants from constants module
from aiida_atomistic.data.structure.constants import (
    _MASS_THRESHOLD,
    _MAGMOM_THRESHOLD,
    _SUM_THRESHOLD,
    _valid_symbols,
    _atomic_masses,
    _atomic_numbers,
)

# Import classes after constants are defined to avoid circular imports
from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder

__all__ = [
    "StructureData",
    "StructureBuilder",
]
