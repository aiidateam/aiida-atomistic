from ase.build import bulk
import numpy as np
import pytest

from aiida_atomistic.data.structure.core import StructureData
from aiida_atomistic.data.structure.mutable import StructureDataMutable
from aiida_atomistic.data.structure.site import Site

"""
General tests for the atomistic StructureData.
The comments the test categories should be replaced by the pytest.mark in the future.
"""

# StructureData initialization:


def test_structure_initialization(example_structure_dict):
    """
    Testing that the StructureData is initialized correctly when:
    (1) nothing is provided;
    (2) properties are provided.
    """

    # (1)
    structure = StructureDataMutable()

    assert isinstance(
        structure, StructureDataMutable
    ), f"Expected type for empty StructureDataMutable: {type(StructureDataMutable)}, \
                                            received: {type(structure)}"

    # (2)
    for structure_type in [StructureDataMutable, StructureData]:
        structure = structure_type(**example_structure_dict)

        assert isinstance(
            structure, structure_type
        ), f"Expected type: {type(structure_type)}, \
                                            received: {type(structure)}"


# StructureData methods:


def test_valid_and_stored_properties(supported_properties, example_structure_dict):
    """
    Testing that the list of valid and stored properties are correct.
    I compare the sets as we don't care about ordering, which will make the test fail even if the
    elements in the two lists are the same.

    NB: if pbc and cell are  not provided, this test will except, as it will then define the default pbc and cell.
    """
    for structure_type in [StructureDataMutable, StructureData]:
        structure = structure_type(**example_structure_dict)

        assert set(structure.get_property_names()) == set(supported_properties)


def test_to_dict_method(example_structure_dict):
    """
    Testing that the StructureData.to_dict() method works properly.

    NB: if pbc and cell are  not provided, this test will except, as it will then define the default pbc and cell.
    """
    for structure_type in [StructureDataMutable, StructureData]:
        structure = structure_type(**example_structure_dict)

        returned_dict = structure.to_dict()

        for derived_property in structure.get_global_properties().keys():
            returned_dict.pop(derived_property, None)
        
        assert (
            returned_dict == example_structure_dict
        ), f"The dictionary returned by the method, {returned_dict}, \
                                                is different from the initial one: {example_structure_dict}"


def test_structure_ASE_initialization():
    """
    Testing that the StructureData is initialized correctly when ASE Atoms object is provided.
    """

    atoms = bulk("Cu", "fcc", a=3.6)
    # test StructureData
    structure = StructureData.from_ase(atoms)

    assert isinstance(structure, StructureData)


def test_to_be_factorized():
    atoms = bulk("Cu", "fcc", a=3.6)
    # test StructureData
    s = StructureData.from_ase(atoms)

    assert isinstance(s._data["pbc"], tuple)
    assert isinstance(s.pbc, np.ndarray)
    assert any(s.pbc)
    assert np.array_equal(
        s.cell, np.array([[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]])
    )
    assert isinstance(s.sites[0], Site)

    with pytest.raises(ValueError):
        s.pbc[0] = False

    with pytest.raises(AttributeError):
        s.pbc = [True, False, True]

    # test StructureDataMutable
    m = StructureDataMutable.from_ase(atoms)

    assert isinstance(m.pbc, np.ndarray)
    assert any(m.pbc)
    assert np.array_equal(
        m.cell, np.array([[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]])
    )
    assert isinstance(m.sites[0], Site)

    # test StructureDataMutable mutability

    assert np.array_equal(m.pbc,np.array([True, True, True]))
    
    with pytest.raises(ValueError):
        m.pbc[0] = 3

    with pytest.raises(AttributeError):
        m.pbc = [False, 4, False]
    
    with pytest.raises(ValueError):
        m.set_pbc([False, "True", False])  
    
    m.set_pbc([False, False, False])
    assert not any(m.pbc)

    # check StructureData and StructureDataMutable give the same properties.
    # in this way I check that it works well.
    m.set_pbc([True, True, True])
    
    returned_dict = s.to_dict()
    for derived_property in s.get_global_properties().keys():
            returned_dict.pop(derived_property, None)
            
    assert returned_dict == m.to_dict()

    # check append_atom works properly
    m.add_atom(
        {
            "symbol": "Cu",
            "mass": 63.546,
            "kind_name": "Cu",
            "position": [1.0, 0.0, -1.0],
            "charge": 0.0,
            "magmom": [0,0,0],
        },
        index=0,
    )
    
    assert np.array_equal(m.get_charges(), np.array([0,0]))


## Test the get_kinds() method.


@pytest.mark.skip
@pytest.fixture
def kinds_properties():
    """
    Return the dictionary of properties as to be used in the tests about the get_kinds() method.
    """
    unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]
    atomic_positions = [
        [0.0, 0.0, 0.0],
        [1.5, 1.5, 1.5],
        [1.5, 2.5, 1.5],
        [1.5, 1.5, 2.5],
    ]
    symbols = ["Li"] * 2 + ["Cu"] * 2
    mass = [6.941] * 2 + [63.546] * 2
    charge = [1, 0.5, 0, 0]

    properties = {
        "cell": {"value": unit_cell},
        "pbc": {"value": [True, True, True]},
        "positions": {
            "value": atomic_positions,
        },
        "symbols": {"value": symbols},
        "mass": {
            "value": mass,
        },
        "charge": {"value": charge},
    }

    return properties


@pytest.mark.skip
def test_get_kinds(example_properties, kinds_properties):

    # (1) trivial system, defaults thr
    structure = StructureData(properties=example_properties)

    kinds, kinds_values = structure.get_kinds()

    assert kinds == ["Li0", "Li1"]
    assert kinds_values["charge"] == [1, 0]

    # (2) trivial system, custom thr
    structure = StructureData(properties=example_properties)

    kinds, kinds_values = structure.get_kinds(custom_thr={"charge": 0.1})

    assert kinds == ["Li0", "Li1"]
    assert kinds_values["charge"] == [1, 0]

    # (3) trivial system, exclude one property
    structure = StructureData(properties=example_properties)

    kinds, kinds_values = structure.get_kinds(exclude=["charge"])

    assert kinds == ["Li0", "Li0"]
    assert kinds_values["mass"] == structure.properties.mass.value
    assert not "charge" in kinds_values.keys()

    # (4) non-trivial system, default thr
    structure = StructureData(properties=kinds_properties)

    kinds, kinds_values = structure.get_kinds(exclude=["charge"])

    assert kinds == ["Li1", "Li1", "Cu2", "Cu2"]
    assert kinds_values["mass"] == structure.properties.mass.value
    assert not "charge" in kinds_values.keys()

    # (5) non-trivial system, custom thr
    structure = StructureData(properties=kinds_properties)

    kinds, kinds_values = structure.get_kinds(custom_thr={"charge": 0.6})

    assert kinds == ["Li0", "Li1", "Cu2", "Cu2"]
    assert kinds_values["mass"] == structure.properties.mass.value
    assert kinds_values["charge"] == [1.0, 0.0, 0.0, 0.0]


# Tests to be skipped because they require the implementation of the related method:


@pytest.mark.skip
def test_structure_pymatgen_initialization():
    """
    Testing that the StructureData is initialized correctly when Pymatgen Atoms object is provided.
    """
    pass
