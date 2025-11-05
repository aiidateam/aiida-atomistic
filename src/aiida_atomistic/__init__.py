"""
aiida_atomistic

AiiDA plugin which contains data and methods for atomistic simulations
"""
from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder

__version__ = "0.1.0a0"

__all__ = [
    "StructureData",
    "StructureBuilder",
]
