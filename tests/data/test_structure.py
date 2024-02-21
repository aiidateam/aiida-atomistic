import pytest
from aiida_atomistic.data.structure import StructureData

"""
General tests for the atomistic StructureData.
"""

@pytest.fixture
def supported_properties():
    """
    Should be updated every time I add properties.
    """
    return ['cell', 'pbc', 'positions',  'symbols', 'mass', 'charge', 'custom']


@pytest.fixture
def example_properties():
    """
    Return the dictionary of properties as to be used in the following tests.
    """
    unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]
    atomic_positions = [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]]
    symbols = ["Li"]*2
    mass = [6.941,6.945]
    charge = [1,0]

    properties = {
        "cell":{"value":unit_cell},
        "pbc":{"value":[True,True,True]},
        "positions":{"value":atomic_positions,},
        "symbols":{"value":symbols},
        "mass":{"value":mass,},
        "charge":{"value":charge}
        }
    
    return properties

@pytest.mark.initialization
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

@pytest.mark.properties_methods
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


@pytest.mark.built_in_methods
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
