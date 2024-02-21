import copy
from aiida_atomistic.data.structure import StructureData
from aiida_atomistic.data.structure.properties.globals.pbc import Pbc


def test_pbc_default(example_properties, default_value = [True,True,True]):
    
    """
    Testing that the pbc default value is stored correctly.
    """
    new_properties = copy.deepcopy(example_properties)
    new_properties.pop("pbc")
    structure = StructureData(
        properties=new_properties
        )

    assert isinstance(structure.properties.pbc, Pbc)
    assert structure.properties.pbc.value == default_value
    assert isinstance(structure.properties.pbc.value, type(default_value))

def test_pbc_set(example_properties, correct_value = [True,False,True]):
    
    """
    Testing that the pbc value is stored correctly.
    """
    new_properties = copy.deepcopy(example_properties)
    new_properties["pbc"]["value"] = correct_value
    structure = StructureData(
        properties=new_properties
        )

    assert isinstance(structure.properties.pbc, Pbc)
    assert structure.properties.pbc.value == correct_value
    assert isinstance(structure.properties.pbc.value, type(correct_value))
    
def test_from_string():
    """Test for the `from_string` method.
    """
    assert Pbc.from_string("3D") == [True,True,True]
    assert Pbc.from_string("0D") == [False,False,False]