import pytest

from typing import Tuple

from ase import Atoms
from aiida_atomistic.data.structure.structure_inherit import StructureData

unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]
atomic_positions = [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]]
symbol = "Li"



def test_structure_bare_initialization():
    
    """
    Testing that the StructureData is initialized correctly when atomic positions, cell are provided.
    """
    
    structure = StructureData(
        cell=unit_cell,
        atomic_positions={"positions":atomic_positions, "symbols":[symbol]*2},
        )

    assert isinstance(structure,StructureData)
    
    
    
def test_structure_ASE_initialization():
    
    """
    Testing that the StructureData is initialized correctly when ASE Atoms object is provided.
    """
    
    atoms = Atoms(symbol*2, atomic_positions, cell = [1,1,1])
    atoms.set_cell(unit_cell, scale_atoms=False)
    atoms.set_pbc([True,False,True])

    structure = StructureData(
        ase=atoms,
        )

    assert isinstance(structure,StructureData)
    