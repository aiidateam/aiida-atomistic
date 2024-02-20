import pytest

from typing import Tuple

from ase import Atoms
from aiida_atomistic.data.structure.structure import StructureData

unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]
atomic_positions = [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]]
symbol = "Li"
mass = [6.941,6.945]
charge = [1,0]

correct_properties = {
    "cell":{"value":unit_cell},
    "pbc":{"value":[True,True,True]},
    "positions":{"value":atomic_positions,},
    "symbols":{"value":symbol*2},
    "mass":{"value":mass,},
    "charge":{"value":charge}
    }

def test_structure_bare_initialization():
    
    """
    Testing that the StructureData is initialized correctly when atomic positions, cell are provided.
    """
    
    structure = StructureData(
        properties=correct_properties
        )

    assert isinstance(structure,StructureData)
    
    
    
'''def test_structure_ASE_initialization():
    
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
'''