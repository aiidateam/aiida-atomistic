import pytest
from aiida_atomistic.data.structure import StructureData

"""
General tests for the atomistic StructureData.
The comments the test categories should be replaced by the pytest.mark in the future.
"""

# StructureData initialization:

def test_structure_initialization(example_properties):
    """
    Testing that the StructureData is initialized correctly when:
    (1) nothing is provided;
    (2) properties are provided.
    """    
    
    # (1)
    structure = StructureData()

    assert isinstance(structure,StructureData), f"Expected type for empty StructureData: {type(StructureData)}, \
                                                  received: {type(structure)}"
    
    # (2)                                          
    structure = StructureData(
        properties=example_properties
        )

    assert isinstance(structure,StructureData), f"Expected type: {type(StructureData)}, \
                                                  received: {type(structure)}"


# StructureData methods:

def test_valid_and_stored_properties(supported_properties,example_properties):
    """
    Testing that the list of valid and stored properties are correct.
    I compare the sets as we don't care about ordering, which will make the test fail even if the
    elements in the two lists are the same.
    
    NB: if pbc and cell are  not provided, this test will except, as it will then define the default pbc and cell.
    """
    structure = StructureData(
        properties=example_properties
        )
    
    assert set(structure.properties.get_supported_properties()) == set(supported_properties)
    assert set(structure.properties.get_stored_properties()) == set(example_properties.keys())



def test_to_dict_method(example_properties):
    """
    Testing that the StructureData.to_dict() method works properly.
    
    NB: if pbc and cell are  not provided, this test will except, as it will then define the default pbc and cell.
    """
    structure = StructureData(
        properties=example_properties
        )
    
    returned_dict = structure.to_dict() 
    
    assert returned_dict == example_properties, f"The dictionary returned by the method, {returned_dict}, \
                                                  is different from the initial one: {example_properties}"    
    
## Test the get_kinds() method.


@pytest.fixture
def kinds_properties():
    """
    Return the dictionary of properties as to be used in the tests about the get_kinds() method.
    """
    unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]
    atomic_positions = [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5],[1.5, 2.5, 1.5],[1.5, 1.5, 2.5]]
    symbols = ["Li"]*2 + ["Cu"]*2
    mass = [6.941]*2 + [63.546]*2
    charge = [1,0.5,0,0]

    properties = {
        "cell":{"value":unit_cell},
        "pbc":{"value":[True,True,True]},
        "positions":{"value":atomic_positions,},
        "symbols":{"value":symbols},
        "mass":{"value":mass,},
        "charge":{"value":charge}
        }
    
    return properties

def test_get_kinds(example_properties, kinds_properties):
    
    # (1) trivial system, defaults thr
    structure = StructureData(
        properties=example_properties
        )
    
    kinds, kinds_values = structure.get_kinds()
    
    assert kinds == ["Li0","Li1"]
    assert kinds_values["charge"] == [1,0]
    
    # (2) trivial system, custom thr
    structure = StructureData(
        properties=example_properties
        )
    
    kinds, kinds_values = structure.get_kinds(custom_thr={"charge": 0.1})
    
    assert kinds == ["Li0","Li1"]
    assert kinds_values["charge"] == [1,0]
    
    # (3) trivial system, exclude one property
    structure = StructureData(
        properties=example_properties
        )
    
    kinds, kinds_values = structure.get_kinds(exclude=["charge"])
    
    assert kinds == ["Li0","Li0"]
    assert kinds_values["mass"] == structure.properties.mass.value
    assert not "charge" in kinds_values.keys()
    
    # (4) non-trivial system, default thr
    structure = StructureData(
        properties=kinds_properties
        )
    
    kinds, kinds_values = structure.get_kinds(exclude=["charge"])
    
    assert kinds == ['Li1', 'Li1', 'Cu2', 'Cu2']
    assert kinds_values["mass"] == structure.properties.mass.value
    assert not "charge" in kinds_values.keys()
    
    # (5) non-trivial system, custom thr
    structure = StructureData(
        properties=kinds_properties
        )
    
    kinds, kinds_values = structure.get_kinds(custom_thr={"charge":0.6})
    
    assert kinds == ['Li0', 'Li1', 'Cu2', 'Cu2']
    assert kinds_values["mass"] == structure.properties.mass.value
    assert kinds_values["charge"] == [1.0, 0.0, 0.0, 0.0]
    
    
    
# Tests to be skipped because they require the implementation of the related method:

@pytest.mark.skip
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
    
@pytest.mark.skip
def test_structure_pymatgen_initialization():
    """
    Testing that the StructureData is initialized correctly when Pymatgen Atoms object is provided.
    """
    pass
