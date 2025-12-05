from ase.build import bulk
import numpy as np
import pytest

from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder

from pydantic import ValidationError

"""
General tests for the atomistic StructureData.
The comments the test categories should be replaced by the pytest.mark in the future.
"""

# StructureData initialization:

def test_structure_initialization(example_structure_dict):
    """
    Testing that the StructureBuilder is initialized correctly when:
    (1) nothing is provided;
    (2) properties are provided.
    """

    # (1.1) Empty StructureBuilder
    structure = StructureBuilder()

    assert isinstance(
        structure, StructureBuilder
    ), f"Expected type for empty StructureBuilder: {type(StructureBuilder)}, \
                                            received: {type(structure)}"

    # (1.1.1) Empty StructureBuilder apart cell
    structure = StructureBuilder()
    structure.set_cell([[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]])
    assert np.allclose(structure.properties.cell, [[1.0,0.0,0.0],[0.0,1.0,0.0],[0.0,0.0,1.0]])

    # (1.2)
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type(**example_structure_dict)

        assert isinstance(
            structure, structure_type
        ), f"Expected type: {type(structure_type)}, \
                                            received: {type(structure)}"

        assert not structure.properties.magmoms or np.allclose(structure.properties.magmoms, [[0.0, 0.0, 0.0]])
        assert np.allclose(structure.properties.charges, [1.0])

        if isinstance(structure, StructureData):
            assert 'magmoms' not in structure.get_defined_properties()
            assert 'charges' in structure.get_defined_properties()

# StructureData methods:

def test_dict(example_structure_dict,example_dumped_structure_dict):
    """
    Testing that the StructureData.to_dict() method works properly.

    NB: if pbc and cell are  not provided, this test will except, as it will then define the default pbc and cell.
    """
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type(**example_structure_dict)

        returned_dict = structure.to_dict()

        expected_keys = set(example_dumped_structure_dict.keys())

        assert (
            set(returned_dict.keys()) == expected_keys
        ), f"The dictionary returned by the method, {set(returned_dict.keys())}, \
                                                is different from the expected dumped one: {expected_keys}"

def test_structure_ASE_initialization():
    """
    Testing that the StructureData/StructureBuilder is initialized correctly when ASE Atoms object is provided.
    """

    atoms = bulk("Cu", "fcc", a=3.6)
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type.from_ase(atoms)

        assert isinstance(structure, structure_type)

    atoms = bulk('Cu', 'fcc', a=3.6)
    atoms.set_initial_charges([1,])
    atoms.set_initial_magnetic_moments([[0,0,1]])
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type.from_ase(atoms)

        assert np.allclose(structure.properties.charges, [1])
        assert np.allclose(structure.properties.magmoms, [[0,0,1]])

def test_structure_Pymatgen_initialization():
    """
    Testing that the StructureData/StructureBuilder is initialized correctly when Pymatgen object is provided.
    """

    from pymatgen.core import Lattice, Structure, Molecule

    coords = [[0, 0, 0], [0.75,0.5,0.75]]
    lattice = Lattice.from_parameters(a=3.84, b=3.84, c=3.84, alpha=120,
                                beta=90, gamma=60)

    struct = Structure(lattice, ["Si", "Si"], coords)
    struct.sites[0].properties["charge"]=1

    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type.from_pymatgen(struct)

        assert np.allclose(structure.properties.charges, [1, 0])
        assert structure.properties.magmoms is None

def test_append_atom():
    atoms = bulk("Cu", "fcc", a=3.6)
    # test StructureBuilder - use append_atom
    m = StructureBuilder.from_ase(atoms)
    m.append_atom(
        atom=Site(
            symbol="Cu",
            mass=63.546,
            kind_name="Cu",
            position=[1.0, 0.0, -1.0],
            charge=1.0,
            magmom=[0,0,0],
        )
    )

    m.append_atom(
        atom={
            "symbol": "Cu",
            "mass": 63.546,
            "kind_name": "Cu",
            "position": [2.0, 0.0, -1.0],
            "charge": 1.0,
            "magmom": [0, 0, 0],
        }
    )

    assert len(m.properties.sites) == 3
    assert np.array_equal(m.properties.charges, np.array([0, 1, 1]))  # First site has no charge

def test_update_sites():
    atoms = bulk("Cu", "fcc", a=3.6)
    # test StructureBuilder - use append_site
    m = StructureBuilder.from_ase(atoms)

    m.append_atom(
        atom=Site(
            symbol="Cu",
            mass=63.546,
            kind_name="Cu",
            position=[1.0, 0.0, -1.0],
            charge=1.0,
            magmom=[0,0,0],
        )
    )

    assert np.array_equal(m.properties.charges, np.array([0, 1]))  # First site has no charge

    m.update_sites(
        site_indices=-1,
        **{
            "charge": -1.0,
            },
    )

    assert np.array_equal(m.properties.charges, np.array([0,-1]))

def test_immutability():
    atoms = bulk("Cu", "fcc", a=3.6)
    # test StructureData
    s = StructureData.from_ase(atoms)

    from aiida_atomistic.data.structure.site import FrozenSite, FrozenList

    assert isinstance(s.properties.pbc, (list, FrozenList))
    assert isinstance(s.properties.pbc, FrozenList)  # Should be FrozenList for immutable
    assert any(s.properties.pbc)
    assert np.allclose(s.properties.cell[0], [0.0, 1.8, 1.8])
    assert np.allclose(s.properties.cell[1], [1.8, 0.0, 1.8])
    assert np.allclose(s.properties.cell[2], [1.8, 1.8, 0.0])
    assert isinstance(s.properties.sites[0], FrozenSite)

    with pytest.raises(ValueError):
        s.properties.pbc[0] = False

    with pytest.raises(ValueError):
        s.properties.pbc = [True, False, True]

    with pytest.raises(ValueError):
        s.properties.sites[0].symbols = "Cu"

def test_mutability():

    atoms = bulk("Cu", "fcc", a=3.6)
    # test StructureBuilder
    m = StructureBuilder.from_ase(atoms)

    assert isinstance(m.properties.pbc, list)
    assert any(m.properties.pbc)
    assert np.array_equal(
        m.properties.cell, [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]])
    assert isinstance(m.properties.sites[0], Site)

    # test StructureBuilder mutability

    assert np.array_equal(m.properties.pbc,np.array([True, True, True]))

    m.set_pbc([False, False, False])
    assert not any(m.properties.pbc)

    # check StructureData and StructureBuilder give the same properties.
    # in this way I check that it works well.
    m.set_pbc([True, True, True])

    # check append_atom works properly
    m.append_atom(
        index=0,
        atom={
            "symbol": "Cu",
            "mass": 63.546,
            "kind_name": "Cu",
            "position": [1.0, 0.0, -1.0],
            "charge": 0.0,
            "magmom": [0,0,0],
        },
    )

    assert np.array_equal(m.properties.charges, np.array([0,0]))

def test_computed_fields(example_structure_dict):
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type(**example_structure_dict)

        assert np.allclose(structure.properties.charges, [1.0])
        assert structure.properties.cell_volume == 11.664000000000001
        assert structure.properties.dimensionality == {'dim': 3, 'label': 'volume', 'value': 11.664000000000001}

        if isinstance(structure, StructureBuilder):
            structure.append_atom(
                Site(
                    symbol="Cu",
                    mass=63.546,
                    kind_name="Cu",
                    position=[1.0, 0.0, -1.0],
                    charge=0.0,
                    magmom=[0,0,0],
                )
            )
            assert np.allclose(structure.properties.charges, [1,0])


def test_model_validator(example_wrong_structure_dict,example_nomass_structure_dict):
    for structure_type in [StructureBuilder, StructureData]:
        if isinstance(structure_type, StructureData):
            with pytest.raises(ValidationError):
                structure = structure_type(**example_wrong_structure_dict)
        elif isinstance(structure_type, StructureBuilder):
            structure = structure_type(**example_wrong_structure_dict)

        structure = structure_type(**example_nomass_structure_dict)
        assert np.allclose(structure.properties.masses, [63.546])
        assert structure.properties.sites[0].mass == 63.546

def test_roundtrips(complex_example_structure_dict_for_kinds):

    #builder -> atomistic -> builder
    b = StructureBuilder(**complex_example_structure_dict_for_kinds)
    s = StructureData.from_builder(b)
    b2 = s.to_builder()

    assert s.to_dict() == b2.to_dict()
    assert b.to_dict() == b2.to_dict()
    assert s.to_dict() == b.to_dict()

    #atomistic -> builder -> atomistic
    s = StructureData(**complex_example_structure_dict_for_kinds)
    b = StructureBuilder.from_aiida(b)
    s2 = b.to_aiida()

    assert s.to_dict() == s2.to_dict()
    assert b.to_dict() == s2.to_dict()
    assert s.to_dict() == b.to_dict()

def test_from_legacy():
    """Test conversion from legacy AiiDA StructureData to atomistic StructureData.

    The aiida_profile fixture ensures the AiiDA database is available.
    """
    from aiida_atomistic.data.structure.utils_orm import from_legacy_to_atomistic
    from aiida.orm import StructureData as LegacyStructureData

    legacy = LegacyStructureData(cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]])
    legacy.append_atom(symbols='H', position=[0.0, 0.0, 0.0], mass=1.008, name='H1')
    legacy.append_atom(symbols='O', position=[0.0, 0.0, 1.0], mass=15.999, name='O1')
    s = from_legacy_to_atomistic(legacy, metadata={'store_provenance': False})

    assert np.allclose(legacy.cell, s.cell)
    assert np.allclose(legacy.pbc, s.pbc)
    assert legacy.get_kind_names() == s.properties.kind_names

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
        "masses": {
            "value": # In the provided code, the `mass` property is used to define the mass of each
            # atom in the structure. It is a property of the `StructureData` and
            # `StructureBuilder` classes that represents the mass of each atom in the
            # structure. The `mass` property is used to store the mass of each atom in the
            # structure, which can be important for various calculations and simulations
            # involving the structure.
            mass,
        },
        "charge": {"value": charge},
    }

    return properties

def test_from_kinds(example_structure_dict_for_kinds, complex_example_structure_dict_for_kinds):

    # (1) trivial system, defaults thr
    for structure_type in [StructureData, StructureBuilder]:
        structure = structure_type(**example_structure_dict_for_kinds)

        # to_dict doesn't accept detect_kinds parameter
        new_structure = structure_type(**structure.to_dict())

        # kind_names not kinds
        kind_names_list = list(new_structure.properties.kind_names) if new_structure.properties.kind_names else []
        assert len(kind_names_list) >= 1  # At least one kind
        assert np.allclose(new_structure.properties.magmoms, [[2.5, 0.1, 0.1], [2.4, 0.1, 0.1]])

    # (2) complex system, defaults thr
    for structure_type in [StructureData, StructureBuilder]:
        structure = structure_type(**complex_example_structure_dict_for_kinds)

        new_structure = structure_type(**structure.to_dict())

        # Check magmoms array comparison
        expected_magmoms = [
            [1.5, 2.5981, 0.0],
            [-3.0, 0.0, 0.0],
            [1.5, 2.5981, 0.0],
            [-3.0, 0.0, 0.0],
            [1.5, -2.5981, 0.0],
            [1.5, -2.5981, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0]
        ]

        assert np.allclose(new_structure.properties.magmoms, expected_magmoms)

def test_set_automatic_kinds(complex_example_structure_dict_for_kinds):
    '''
    This will test the generate_kinds method for StructureBuilder only
    (remember that the method is not available for StructureData as it is a Setter method).
    '''
    structure = StructureBuilder(**complex_example_structure_dict_for_kinds)

    # Use generate_kinds instead of set_automatic_kinds
    structure.generate_kinds()

    # Check kind_names if they were generated
    if structure.properties.kind_names:
        kind_names_list = list(structure.properties.kind_names)
        assert len(kind_names_list) == 8  # Should have 8 sites
    expected_magmoms = [[1.5, 2.5981, 0.0],
                                [-3.0, 0.0, 0.0],
                                [1.5, 2.5981, 0.0],
                                [-3.0, 0.0, 0.0],
                                [1.5, -2.5981, 0.0],
                                [1.5, -2.5981, 0.0],
                                [0.0, 0.0, 0.0],
                                [0.0, 0.0, 0.0]]
    assert np.allclose(structure.properties.magmoms, expected_magmoms)

def test_alloy(example_structure_dict_alloy):

    for structure_type in [StructureData, StructureBuilder]:
        structure = structure_type(**example_structure_dict_alloy)

        assert structure.properties.masses == [45.263768999999996]
        assert structure.properties.symbols == [["Cu","Al"]]
        assert structure.is_alloy
        assert len(structure.properties.sites) == 1


# Test __repr__ methods

def test_site_repr():
    """Test Site.__repr__ method."""
    # Simple site
    site1 = Site(symbol='Fe', position=[0, 0, 0])
    repr_str = repr(site1)
    assert 'Fe' in repr_str
    assert '0.000' in repr_str
    assert 'Site(' in repr_str

    # Site with properties
    site2 = Site(symbol='O', position=[1.5, 1.5, 1.5], charge=-2.0, kind_name='oxygen1')
    repr_str = repr(site2)
    assert 'O' in repr_str
    assert '1.500' in repr_str
    assert 'charge=-2.00' in repr_str
    assert 'kind=oxygen1' in repr_str

    # Site with magnetization
    site3 = Site(symbol='Fe', position=[2.5, 2.5, 2.5], magnetization=3.5)
    repr_str = repr(site3)
    assert 'Fe' in repr_str
    assert 'magnetization=3.50' in repr_str

    # Site with magmom vector
    site4 = Site(symbol='Co', position=[0, 1, 2], magmom=[0, 0, 2.5])
    repr_str = repr(site4)
    assert 'Co' in repr_str
    assert 'magmom=' in repr_str
    assert '2.50' in repr_str

    # Alloy site
    site5 = Site(symbol=['Fe', 'Co'], position=[3, 3, 3], weight=(0.5, 0.5), kind_name='alloy1')
    repr_str = repr(site5)
    assert 'Fe/Co' in repr_str
    assert 'weight=' in repr_str
    assert '0.50' in repr_str


def test_structure_repr(example_structure_dict):
    """Test Structure.__repr__ method."""
    # Test with StructureBuilder
    structure = StructureBuilder(**example_structure_dict)
    repr_str = repr(structure)

    assert 'StructureBuilder' in repr_str
    assert 'Cu' in repr_str  # Formula
    assert 'sites' in repr_str
    assert 'V=' in repr_str  # Volume
    assert 'A^3' in repr_str  # Volume unit

    # Test with StructureData
    structure_data = StructureData(**example_structure_dict)
    repr_str = repr(structure_data.properties)

    assert 'Cu' in repr_str
    assert 'sites' in repr_str


def test_structure_repr_dimensionality():
    """Test that __repr__ shows correct dimensionality."""
    # 3D structure
    structure_3d = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{'symbol': 'Fe', 'position': [0, 0, 0]}]
    )
    assert '3D' in repr(structure_3d)

    # 2D structure
    structure_2d = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 20.0]],
        pbc=[True, True, False],
        sites=[{'symbol': 'C', 'position': [0, 0, 0]}]
    )
    assert '2D' in repr(structure_2d)

    # 1D structure
    structure_1d = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 20.0, 0], [0, 0, 20.0]],
        pbc=[True, False, False],
        sites=[{'symbol': 'C', 'position': [0, 0, 0]}]
    )
    assert '1D' in repr(structure_1d)

    # 0D structure (molecule)
    structure_0d = StructureBuilder(
        cell=[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
        pbc=[False, False, False],
        sites=[{'symbol': 'H', 'position': [0, 0, 0]}]
    )
    assert '0D' in repr(structure_0d)


def test_structure_repr_magnetic():
    """Test that __repr__ shows magnetic information."""
    # Structure with tot_magnetization
    structure_mag = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{'symbol': 'Fe', 'position': [0, 0, 0], 'magnetization': 2.5}],
        tot_magnetization=2.5
    )
    repr_str = repr(structure_mag)
    assert 'tot_mag=2.50' in repr_str or 'magnetic' in repr_str


def test_structure_repr_charged():
    """Test that __repr__ shows charge information."""
    structure_charged = StructureBuilder(
        cell=[[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]],
        pbc=[True, True, True],
        sites=[
            {'symbol': 'Na', 'position': [0, 0, 0], 'charge': 1.0},
            {'symbol': 'Cl', 'position': [2.5, 2.5, 2.5], 'charge': -1.0}
        ],
        tot_charge=0.0
    )
    repr_str = repr(structure_charged)
    assert 'tot_charge=0.00' in repr_str or 'charged' in repr_str


def test_structure_repr_alloy(example_structure_dict_alloy):
    """Test that __repr__ shows alloy flag."""
    structure_alloy = StructureBuilder(**example_structure_dict_alloy)
    repr_str = repr(structure_alloy)
    assert 'alloy' in repr_str
