from aiida_atomistic.data.structure import StructureData

unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]
atomic_positions = [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]]
symbols = ["Li"]*2

correct_properties = {
    "cell":{"value":unit_cell},
    "positions":{"value":atomic_positions,},
    "symbols":{"value":symbols},
    "pbc":{"value":[True,False,True]},
    }


def test_pbc_default(default_value = [True,True,True]):
    
    """
    Testing that the pbc default value is stored correctly.
    """
    import copy
    new_properties = copy.deepcopy(correct_properties)
    new_properties.pop("pbc")
    structure = StructureData(
        properties=new_properties
        )

    assert structure.properties.pbc.value == default_value, f"default value should be {default_value}, and not {structure.properties.pbc.value}"
    assert isinstance(structure.properties.pbc.value, type(default_value)), f"type of the value should be {type(default_value)}, not {type(structure.properties.pbc.value)}" 

def test_pbc_set(correct_value = [True,False,True]):
    
    """
    Testing that the pbc value is stored correctly.
    """
    
    structure = StructureData(
        properties=correct_properties
        )

    assert structure.properties.pbc.value == correct_value, f"value should be {correct_value}, and not {structure.properties.pbc.value}"
    assert isinstance(structure.properties.pbc.value, type(correct_value)), f"type of the value should be {type(correct_value)}, not {type(structure.properties.pbc.value)}"    
    