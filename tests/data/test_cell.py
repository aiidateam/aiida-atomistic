import copy
from aiida_atomistic.data.structure import StructureData


def test_cell_default(example_properties, default_value = [[0,0,0]]*3):
    
    """
    Testing that the cell default value is stored correctly.
    """
    new_properties = copy.deepcopy(example_properties)
    new_properties.pop("cell")
    structure = StructureData(
        properties=new_properties
        )

    assert structure.properties.cell.value == default_value
    assert isinstance(structure.properties.cell.value, type(default_value))

def test_cell_set(example_properties, correct_value = [[1,0,0]]*3):
    
    """
    Testing that the cell value is stored correctly.
    """
    new_properties = copy.deepcopy(example_properties)
    new_properties["cell"]["value"] = correct_value
    structure = StructureData(
        properties=new_properties
        )

    assert structure.properties.cell.value == correct_value
    assert isinstance(structure.properties.cell.value, type(correct_value))