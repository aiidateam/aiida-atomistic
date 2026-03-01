"""
aiida_atomistic

AiiDA plugin which contains data and methods for atomistic simulations
"""

__version__ = "0.1.0a0"

import typing as t

try:
    import ase  # noqa: F401

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


# Import classes after constants are defined to avoid circular imports
from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder

__all__ = [
    "StructureData",
    "StructureBuilder",
]
