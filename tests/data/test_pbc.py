import pytest

from typing import Tuple

from ase import Atoms
from aiida_atomistic.data.structure.structure_inherit import StructureData

unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]

atoms = Atoms('LiLi', [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]], cell = [1,1,1])
atoms.set_cell(unit_cell, scale_atoms=False)
atoms.set_pbc([True,True,True])


def test_pbc_set(correct_value = (True,False,True)):
    
    """
    Testing that the pbc value is stored correctly.
    """
    
    structure = StructureData(
        ase=atoms,
        properties={
                'pbc': {'value':correct_value},
                },
        )

    assert structure.properties.pbc.value == correct_value, f"value should be {correct_value}"
    assert isinstance(structure.properties.pbc.value, type(correct_value)), "type of the value should be {type(correct_value)}"
    assert structure.properties.pbc.value == structure.pbc, f"structure.properties.pbc.value={structure.properties.pbc.value}, structure.pbc={structure.pbc}"
    
    
def test_pbc_immutability(correct_value = (True,False,True)):
    
    """
    Testing that the pbc property is immutable.
    """
    
    structure = StructureData(
        ase=atoms,
        properties={
                'pbc': {'value':correct_value},
                },
        )

    with pytest.raises(NotImplementedError):
        structure.properties.pbc = {"value":[True,False,True]}, f"pbc cannot be changed after the initialization"
    