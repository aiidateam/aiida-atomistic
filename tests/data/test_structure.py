from ase.build import bulk
import numpy as np
import pytest

from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder
from aiida_atomistic.data.structure.site import Site, FrozenSite, FrozenList

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

    assert isinstance(structure, StructureBuilder), (
        f"Expected type for empty StructureBuilder: {type(StructureBuilder)}, \
                                            received: {type(structure)}"
    )

    # (1.1.1) Empty StructureBuilder apart cell
    structure = StructureBuilder()
    structure.set_cell([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    assert np.allclose(
        structure.properties.cell, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    )

    # (1.2)
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type(**example_structure_dict)

        assert isinstance(structure, structure_type), (
            f"Expected type: {type(structure_type)}, \
                                            received: {type(structure)}"
        )

        assert not structure.properties.magmoms or np.allclose(
            structure.properties.magmoms, [[0.0, 0.0, 0.0]]
        )
        assert np.allclose(structure.properties.charges, [1.0])

        if isinstance(structure, StructureData):
            assert "magmoms" not in structure.get_defined_properties()
            assert "charges" in structure.get_defined_properties()


# StructureData methods:


def test_dict(example_structure_dict, example_dumped_structure_dict):
    """
    Testing that the StructureData.to_dict() method works properly.

    NB: if pbc and cell are  not provided, this test will except, as it will then define the default pbc and cell.
    """
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type(**example_structure_dict)

        returned_dict = structure.to_dict()

        expected_keys = set(example_dumped_structure_dict.keys())

        assert set(returned_dict.keys()) == expected_keys, (
            f"The dictionary returned by the method, {set(returned_dict.keys())}, \
                                                is different from the expected dumped one: {expected_keys}"
        )


def test_structure_ASE_initialization():
    """
    Testing that the StructureData/StructureBuilder is initialized correctly when ASE Atoms object is provided.
    """

    atoms = bulk("Cu", "fcc", a=3.6)
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type.from_ase(atoms)

        assert isinstance(structure, structure_type)

    atoms = bulk("Cu", "fcc", a=3.6)
    atoms.set_initial_charges(
        [
            1,
        ]
    )
    atoms.set_initial_magnetic_moments([[0, 0, 1]])
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type.from_ase(atoms)

        assert np.allclose(structure.properties.charges, [1])
        assert np.allclose(structure.properties.magmoms, [[0, 0, 1]])


def test_structure_Pymatgen_initialization():
    """
    Testing that the StructureData/StructureBuilder is initialized correctly when Pymatgen object is provided.
    """

    from pymatgen.core import Lattice, Structure

    coords = [[0, 0, 0], [0.75, 0.5, 0.75]]
    lattice = Lattice.from_parameters(
        a=3.84, b=3.84, c=3.84, alpha=120, beta=90, gamma=60
    )

    struct = Structure(lattice, ["Si", "Si"], coords)
    struct.sites[0].properties["charge"] = 1

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
            magmom=[0, 0, 0],
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
    assert np.array_equal(
        m.properties.charges, np.array([0, 1, 1])
    )  # First site has no charge


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
            magmom=[0, 0, 0],
        )
    )

    assert np.array_equal(
        m.properties.charges, np.array([0, 1])
    )  # First site has no charge

    m.update_sites(
        site_indices=-1,
        **{
            "charge": -1.0,
        },
    )

    assert np.array_equal(m.properties.charges, np.array([0, -1]))


def test_immutability():
    atoms = bulk("Cu", "fcc", a=3.6)
    # test StructureData
    s = StructureData.from_ase(atoms)

    assert isinstance(s.properties.pbc, (list, FrozenList))
    assert isinstance(
        s.properties.pbc, FrozenList
    )  # Should be FrozenList for immutable
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
        m.properties.cell, [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]]
    )
    assert isinstance(m.properties.sites[0], Site)

    # test StructureBuilder mutability

    assert np.array_equal(m.properties.pbc, np.array([True, True, True]))

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
            "magmom": [0, 0, 0],
        },
    )

    assert np.array_equal(m.properties.charges, np.array([0, 0]))


def test_computed_fields(example_structure_dict):
    for structure_type in [StructureBuilder, StructureData]:
        structure = structure_type(**example_structure_dict)

        assert np.allclose(structure.properties.charges, [1.0])
        assert structure.properties.cell_volume == 11.664000000000001
        assert structure.properties.dimensionality == {
            "dim": 3,
            "label": "volume",
            "value": 11.664000000000001,
        }

        if isinstance(structure, StructureBuilder):
            structure.append_atom(
                Site(
                    symbol="Cu",
                    mass=63.546,
                    kind_name="Cu",
                    position=[1.0, 0.0, -1.0],
                    charge=0.0,
                    magmom=[0, 0, 0],
                )
            )
            assert np.allclose(structure.properties.charges, [1, 0])


def test_model_validator(example_wrong_structure_dict, example_nomass_structure_dict):
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

    # builder -> atomistic -> builder
    b = StructureBuilder(**complex_example_structure_dict_for_kinds)
    s = StructureData.from_builder(b)
    b2 = s.to_builder()

    assert s.to_dict() == b2.to_dict()
    assert b.to_dict() == b2.to_dict()
    assert s.to_dict() == b.to_dict()

    # atomistic -> builder -> atomistic
    s = StructureData(**complex_example_structure_dict_for_kinds)
    b = StructureBuilder.from_aiida(s)
    s2 = b.to_aiida()

    assert s.to_dict() == s2.to_dict()
    assert b.to_dict() == s2.to_dict()
    assert s.to_dict() == b.to_dict()


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
            "value":  # In the provided code, the `mass` property is used to define the mass of each
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


def test_from_kinds(
    example_structure_dict_for_kinds, complex_example_structure_dict_for_kinds
):

    # (1) trivial system, defaults thr
    for structure_type in [StructureData, StructureBuilder]:
        structure = structure_type(**example_structure_dict_for_kinds)

        # to_dict doesn't accept detect_kinds parameter
        new_structure = structure_type(**structure.to_dict())

        # kind_names not kinds
        kind_names_list = (
            list(new_structure.properties.kind_names)
            if new_structure.properties.kind_names
            else []
        )
        assert len(kind_names_list) >= 1  # At least one kind
        assert np.allclose(
            new_structure.properties.magmoms, [[2.5, 0.1, 0.1], [2.4, 0.1, 0.1]]
        )

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
            [0.0, 0.0, 0.0],
        ]

        assert np.allclose(new_structure.properties.magmoms, expected_magmoms)


def test_set_automatic_kinds(complex_example_structure_dict_for_kinds):
    """
    This will test the to_kinds method for StructureBuilder only
    (remember that the method is not available for StructureData as it is a Setter method).
    The to_kinds method groups sites by kind, so the order may be different from input.
    """
    structure = StructureBuilder(**complex_example_structure_dict_for_kinds)

    # Use to_kinds to group sites by kind
    structure = structure.to_kinds()

    # Check kind_names if they were generated
    if structure.properties.kind_names:
        kind_names_list = list(structure.properties.kind_names)
        assert len(kind_names_list) == 8  # Should have 8 sites

    # After to_kinds(), sites are grouped by kind, so the order changes
    # The expected magmoms reflect the grouped order
    expected_magmoms = [
        [1.5, 2.5981, 0.0],
        [1.5, 2.5981, 0.0],
        [-3.0, 0.0, 0.0],
        [-3.0, 0.0, 0.0],
        [1.5, -2.5981, 0.0],
        [1.5, -2.5981, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    assert np.allclose(structure.properties.magmoms, expected_magmoms)


def test_alloy(example_structure_dict_alloy):

    for structure_type in [StructureData, StructureBuilder]:
        structure = structure_type(**example_structure_dict_alloy)

        assert structure.properties.masses == [45.263768999999996]
        assert structure.properties.symbols == [["Cu", "Al"]]
        assert structure.is_alloy
        assert len(structure.properties.sites) == 1


# Test __repr__ methods


def test_site_repr():
    """Test Site.__repr__ method."""
    # Simple site
    site1 = Site(symbol="Fe", position=[0, 0, 0])
    repr_str = repr(site1)
    assert "Fe" in repr_str
    assert "0.000" in repr_str
    assert "Site(" in repr_str

    # Site with properties
    site2 = Site(symbol="O", position=[1.5, 1.5, 1.5], charge=-2.0, kind_name="oxygen1")
    repr_str = repr(site2)
    assert "O" in repr_str
    assert "1.500" in repr_str
    assert "charge=-2.00" in repr_str
    assert "kind=oxygen1" in repr_str

    # Site with magnetization
    site3 = Site(symbol="Fe", position=[2.5, 2.5, 2.5], magnetization=3.5)
    repr_str = repr(site3)
    assert "Fe" in repr_str
    assert "magnetization=3.50" in repr_str

    # Site with magmom vector
    site4 = Site(symbol="Co", position=[0, 1, 2], magmom=[0, 0, 2.5])
    repr_str = repr(site4)
    assert "Co" in repr_str
    assert "magmom=" in repr_str
    assert "2.50" in repr_str

    # Alloy site
    site5 = Site(
        symbol=["Fe", "Co"], position=[3, 3, 3], weight=(0.5, 0.5), kind_name="alloy1"
    )
    repr_str = repr(site5)
    assert "Fe_Co" in repr_str
    assert "weight=" in repr_str
    assert "0.50" in repr_str


def test_structure_repr(example_structure_dict):
    """Test Structure.__repr__ method."""
    # Test with StructureBuilder
    structure = StructureBuilder(**example_structure_dict)
    repr_str = repr(structure)

    assert "StructureBuilder" in repr_str
    assert "Cu" in repr_str  # Formula
    assert "sites" in repr_str
    assert "V=" in repr_str  # Volume
    assert "A^3" in repr_str  # Volume unit

    # Test with StructureData
    structure_data = StructureData(**example_structure_dict)
    repr_str = repr(structure_data.properties)

    assert "Cu" in repr_str
    assert "sites" in repr_str


def test_structure_repr_dimensionality():
    """Test that __repr__ shows correct dimensionality."""
    # 3D structure
    structure_3d = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )
    assert "3D" in repr(structure_3d)

    # 2D structure
    structure_2d = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 20.0]],
        pbc=[True, True, False],
        sites=[{"symbol": "C", "position": [0, 0, 0]}],
    )
    assert "2D" in repr(structure_2d)

    # 1D structure
    structure_1d = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 20.0, 0], [0, 0, 20.0]],
        pbc=[True, False, False],
        sites=[{"symbol": "C", "position": [0, 0, 0]}],
    )
    assert "1D" in repr(structure_1d)

    # 0D structure (molecule)
    structure_0d = StructureBuilder(
        cell=[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
        pbc=[False, False, False],
        sites=[{"symbol": "H", "position": [0, 0, 0]}],
    )
    assert "0D" in repr(structure_0d)


def test_structure_repr_magnetic():
    """Test that __repr__ shows magnetic information."""
    # Structure with tot_magnetization
    structure_mag = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0], "magnetization": 2.5}],
        tot_magnetization=2.5,
    )
    repr_str = repr(structure_mag)
    assert "tot_mag=2.50" in repr_str or "magnetic" in repr_str


def test_structure_repr_charged():
    """Test that __repr__ shows charge information."""
    structure_charged = StructureBuilder(
        cell=[[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Na", "position": [0, 0, 0], "charge": 1.0},
            {"symbol": "Cl", "position": [2.5, 2.5, 2.5], "charge": -1.0},
        ],
        tot_charge=0.0,
    )
    repr_str = repr(structure_charged)
    assert "tot_charge=0.00" in repr_str or "charged" in repr_str


def test_structure_repr_alloy(example_structure_dict_alloy):
    """Test that __repr__ shows alloy flag."""
    structure_alloy = StructureBuilder(**example_structure_dict_alloy)
    repr_str = repr(structure_alloy)
    assert "alloy" in repr_str


# Coverage improvement tests


def test_is_numeric_array_with_ndarray():
    """Test _is_numeric_array with numpy array."""
    assert StructureData._is_numeric_array(np.array([1, 2, 3]))
    assert StructureData._is_numeric_array(np.array([1.0, 2.0, 3.0]))
    assert StructureData._is_numeric_array(np.array([[1, 2], [3, 4]]))


def test_is_numeric_array_with_list():
    """Test _is_numeric_array with list."""
    assert StructureData._is_numeric_array([1, 2, 3])
    assert StructureData._is_numeric_array([1.0, 2.0, 3.0])
    assert StructureData._is_numeric_array([[1, 2], [3, 4]])


def test_is_numeric_array_with_non_numeric():
    """Test _is_numeric_array with non-numeric values."""
    assert not StructureData._is_numeric_array(["a", "b", "c"])
    assert not StructureData._is_numeric_array([True, False])
    assert not StructureData._is_numeric_array("string")
    assert not StructureData._is_numeric_array(42)


def test_get_queryable_properties_basic():
    """Test basic queryable properties retrieval."""
    props = StructureData.get_queryable_properties()

    assert "queryable" in props
    assert "not_queryable" in props
    assert isinstance(props["queryable"], list)
    assert isinstance(props["not_queryable"], list)

    # Check that common properties are in correct categories
    assert "cell" in props["queryable"]
    assert "pbc" in props["queryable"]
    # composition is stored in db and is queryable; formula is not stored
    assert "composition" in props["queryable"]
    assert "formula" not in props["queryable"]

    # Arrays stored in npz should not be queryable
    assert "positions" in props["not_queryable"]
    assert "charges" in props["not_queryable"]


def test_get_queryable_properties_include_internal():
    """Test get_queryable_properties with include_internal=True."""
    props_with = StructureData.get_queryable_properties(include_internal=True)
    props_without = StructureData.get_queryable_properties(include_internal=False)

    # Sites and kinds should be included when include_internal=True
    all_props_with = set(props_with["queryable"]) | set(props_with["not_queryable"])
    all_props_without = set(props_without["queryable"]) | set(
        props_without["not_queryable"]
    )

    assert "sites" in all_props_with
    assert "sites" in all_props_without  # Always in not_queryable


def test_print_queryable_properties(capsys):
    """Test that print_queryable_properties produces output."""
    StructureData.print_queryable_properties()

    captured = capsys.readouterr()
    assert "Queryable Properties" in captured.out
    assert "QUERYABLE" in captured.out
    assert "NOT QUERYABLE" in captured.out
    assert "QueryBuilder" in captured.out


def test_detect_storage_backend_for_regular_fields():
    """Test storage backend detection for regular fields."""
    # Test for fields with different storage backends
    backend = StructureData.detect_storage_backend("cell")
    assert backend in ["db", "attribute", "attributes", ""]

    backend = StructureData.detect_storage_backend("positions")
    assert backend in ["npz", "repo", "repository", "db"]


def test_detect_storage_backend_for_computed_fields():
    """Test storage backend detection for computed fields."""
    # composition is stored in db
    backend = StructureData.detect_storage_backend("composition")
    assert backend in ["db", "attribute", "attributes"]


def test_composition_field():
    """composition is a queryable dict of element → count."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Fe", "position": [0, 0, 0]},
            {"symbol": "O", "position": [1, 0, 0]},
            {"symbol": "O", "position": [2, 0, 0]},
        ],
    )
    comp = structure.properties.composition
    assert isinstance(comp, dict)
    assert comp["Fe"] == 1
    assert comp["O"] == 2
    assert len(comp) == 2


def test_composition_alloy():
    """composition accumulates weighted counts for alloy sites."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            # alloy site: 50 % Fe, 50 % Mn
            {"symbol": ["Fe", "Mn"], "weight": (0.5, 0.5), "position": [0, 0, 0]},
            {"symbol": "O", "position": [1, 0, 0]},
        ],
    )
    comp = structure.properties.composition
    assert comp["Fe"] == 0.5
    assert comp["Mn"] == 0.5
    assert comp["O"] == 1


def test_composition_vacancy():
    """composition omits the vacancy (zero-weight) contribution."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            # 70 % Fe, 30 % vacancy → only Fe appears, with weight 0.7
            {"symbol": "Fe", "weight": (0.7,), "position": [0, 0, 0]},
            {"symbol": "O", "position": [1, 0, 0]},
        ],
    )
    comp = structure.properties.composition
    assert abs(comp["Fe"] - 0.7) < 1e-6
    assert comp["O"] == 1
    assert len(comp) == 2  # no phantom vacancy element


def test_kinds_alloy_with_kind_name():
    """kinds must not crash when alloy sites have an explicit kind_name."""
    from aiida_atomistic.data.structure.structure import StructureBuilder

    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            # alloy site with an explicit kind_name
            {
                "symbol": ["Fe", "Mn"],
                "weight": (0.5, 0.5),
                "position": [0, 0, 0],
                "kind_name": "FeMn1",
            },
            {"symbol": "O", "position": [1, 0, 0], "kind_name": "O1"},
        ],
    )
    kinds = builder.kinds
    assert kinds is not None
    kind_names = {k.kind_name for k in kinds}
    assert "FeMn1" in kind_names
    assert "O1" in kind_names


def test_kinds_alloy_without_kind_name():
    """kinds falls back to 'Fe_Mn' string for alloy sites with no kind_name."""
    from aiida_atomistic.data.structure.structure import StructureBuilder

    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": ["Fe", "Mn"], "weight": (0.5, 0.5), "position": [0, 0, 0]},
            {"symbol": "O", "position": [1, 0, 0], "kind_name": "O"},
        ],
    )
    # must not raise TypeError: unhashable type 'list'
    kinds = builder.kinds
    assert kinds is not None
    kind_names = {k.kind_name for k in kinds}
    assert "Fe_Mn" in kind_names


def test_mass_alloy_site():
    """Mass of an alloy site is the weight-average of elemental masses."""
    from aiida_atomistic.data.structure.structure import StructureBuilder
    from aiida_atomistic.data.structure.constants import _atomic_masses  # noqa: PLC0415

    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": ["Fe", "Mn"], "weight": (0.5, 0.5), "position": [0, 0, 0]},
        ],
    )
    expected = 0.5 * _atomic_masses["Fe"] + 0.5 * _atomic_masses["Mn"]
    assert abs(builder.properties.sites[0].mass - expected) < 1e-6


def test_mass_vacancy_site():
    """Mass of a vacancy site is the elemental mass weighted by occupation."""
    from aiida_atomistic.data.structure.structure import StructureBuilder
    from aiida_atomistic.data.structure.constants import _atomic_masses  # noqa: PLC0415

    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Fe", "weight": (0.7,), "position": [0, 0, 0]},
        ],
    )
    expected = 0.7 * _atomic_masses["Fe"]
    assert abs(builder.properties.sites[0].mass - expected) < 1e-6


def test_composition_stored_as_attribute(aiida_profile_clean):
    """After storing, composition appears as a DB attribute."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Fe", "position": [0, 0, 0]},
            {"symbol": "O", "position": [1, 0, 0]},
        ],
    )
    structure.store()
    attrs = dict(structure.base.attributes.all)
    assert "composition" in attrs
    assert attrs["composition"]["Fe"] == 1
    assert attrs["composition"]["O"] == 1
    # formula must NOT be stored as an attribute
    assert "formula" not in attrs


def test_formula_not_in_attributes(aiida_profile_clean):
    """formula is a plain property and must never appear in DB attributes."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Cu", "position": [0, 0, 0]}],
    )
    structure.store()
    assert "formula" not in dict(structure.base.attributes.all)
    # but it is still accessible as a plain property
    assert structure.properties.formula == "Cu"


def test_detect_storage_backend_for_unknown():
    """Test storage backend detection for unknown properties."""
    backend = StructureData.detect_storage_backend("unknown_property")
    assert backend == "db"  # Default


def test_store_properties_with_arrays(aiida_profile_clean):
    """Test storing properties with numpy arrays."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
            {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
        ],
    )

    # Should have stored attributes
    assert structure.base.attributes.all

    # Should have stored npz file
    assert (
        structure._properties_filename in structure.base.repository.list_object_names()
    )


def test_store_properties_with_kind_compression(aiida_profile_clean):
    """Test storing properties with kind-based compression."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1", "charge": 2.0},
            {
                "symbol": "Fe",
                "position": [1.5, 1.5, 1.5],
                "kind_name": "Fe1",
                "charge": 2.0,
            },
        ],
    )

    # Should have kind_names in attributes
    assert "n_kinds" in structure.base.attributes.all
    assert structure.base.attributes.all["n_kinds"] == 1


def test_load_properties_from_npz(aiida_profile_clean):
    """Test loading properties from npz file."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
            {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
        ],
    )

    # Store it
    structure.store()

    # Load properties
    props = structure._load_properties_from_npz()

    # Should have positions and charges
    assert "positions" in props
    assert "charges" in props


def test_load_properties_from_npz_no_file(aiida_profile_clean):
    """Test loading when no npz file exists."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    # Should return empty dict
    props = structure._load_properties_from_npz()
    assert isinstance(props, dict)


def test_npz_deterministic_key_order(aiida_profile_clean):
    """Test that NPZ files have deterministic key ordering for stable hashing."""

    # Create a structure with multiple properties that will be stored in repository
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {
                "symbol": "Fe",
                "position": [0, 0, 0],
                "charge": 2.0,
                "magmom": [0, 0, 2.2],
            },
            {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -1.0},
        ],
    )
    structure.store()

    # Load the NPZ file and check key order
    npz_data = structure._load_properties_from_npz()

    # Keys should be present (exact keys depend on what gets stored in repository)
    assert len(npz_data) > 0, "NPZ should contain data"

    # Get the keys as a list
    keys = list(npz_data.keys())

    # Keys should be in sorted order
    assert keys == sorted(keys), f"NPZ keys should be sorted, but got: {keys}"

    # Create another identical structure - should have same key order
    structure2 = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {
                "symbol": "Fe",
                "position": [0, 0, 0],
                "charge": 2.0,
                "magmom": [0, 0, 2.2],
            },
            {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -1.0},
        ],
    )
    structure2.store()

    npz_data2 = structure2._load_properties_from_npz()
    keys2 = list(npz_data2.keys())

    # Key order should be identical
    assert keys == keys2, "Identical structures should have same NPZ key order"

    # Repository hashes should match (deterministic binary output)
    hash1 = structure.base.repository.hash()
    hash2 = structure2.base.repository.hash()
    assert hash1 == hash2, (
        "Identical structures should have identical repository hashes"
    )


def test_properties_getter_unstored():
    """Test properties getter for unstored node."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    # Should return _properties
    assert structure.properties is structure._properties


def test_properties_getter_stored(aiida_profile_clean):
    """Test properties getter for stored node."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[
            {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
        ],
    )

    structure.store()

    # Should reconstruct from stored data
    props = structure.properties
    assert props is not None
    assert np.allclose(props.cell, [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]])


def test_properties_getter_cached(aiida_profile_clean):
    """Test that properties getter uses cache."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    structure.store()

    # First access
    props1 = structure.properties

    # Second access should return same instance (cached)
    props2 = structure.properties
    assert props1 is props2


def test_from_builder():
    """Test from_builder class method."""
    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    structure = StructureData.from_builder(builder)
    assert isinstance(structure, StructureData)
    assert np.allclose(structure.properties.cell, builder.properties.cell)


def test_from_builder_invalid():
    """Test from_builder with invalid input."""
    with pytest.raises(
        ValueError, match="Input builder should be of type StructureBuilder"
    ):
        StructureData.from_builder("not a builder")


def test_to_builder():
    """Test to_builder method."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    builder = structure.to_builder()
    assert isinstance(builder, StructureBuilder)
    assert np.allclose(builder.properties.cell, structure.properties.cell)


def test_builder_from_aiida():
    """Test StructureBuilder.from_aiida method."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    builder = StructureBuilder.from_aiida(structure)
    assert isinstance(builder, StructureBuilder)


def test_builder_from_aiida_invalid():
    """Test StructureBuilder.from_aiida with invalid input."""
    with pytest.raises(ValueError, match="Input aiida should be of type"):
        StructureBuilder.from_aiida("not a structure")


def test_builder_to_aiida():
    """Test StructureBuilder.to_aiida method."""
    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    structure = builder.to_aiida()
    assert isinstance(structure, StructureData)
    assert np.allclose(structure.properties.cell, builder.properties.cell)


def test_structuredata_repr_unstored():
    """Test StructureData repr for unstored node."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    repr_str = repr(structure)
    assert "StructureData" in repr_str
    assert "uuid" in repr_str
    assert "unstored" in repr_str
    assert "Fe" in repr_str


def test_structuredata_repr_stored(aiida_profile_clean):
    """Test StructureData repr for stored node."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    structure.store()

    repr_str = repr(structure)
    assert "StructureData" in repr_str
    assert "uuid" in repr_str
    assert "pk" in repr_str
    assert "Fe" in repr_str


def test_structuredata_str():
    """Test StructureData __str__ method."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    str_repr = str(structure)
    assert str_repr == repr(structure)


def test_structurebuilder_repr():
    """Test StructureBuilder repr."""
    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    repr_str = repr(builder)
    assert "StructureBuilder" in repr_str
    assert "Fe" in repr_str


def test_structurebuilder_str():
    """Test StructureBuilder __str__ method."""
    builder = StructureBuilder(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    str_repr = str(builder)
    assert str_repr == repr(builder)


def test_validate_with_shape_metadata(aiida_profile_clean):
    """Test validation with shape metadata."""
    # Create a structure with shape metadata enabled
    StructureData._store_shape_metadata = True

    try:
        structure = StructureData(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
            ],
        )

        structure.store()

        # Validation should pass
        assert structure._validate()
    finally:
        # Reset to default
        StructureData._store_shape_metadata = False


def test_validate_no_shape_metadata(aiida_profile_clean):
    """Test validation without shape metadata."""
    structure = StructureData(
        cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        pbc=[True, True, True],
        sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
    )

    structure.store()

    # Validation should pass
    assert structure._validate()


# ---------------------------------------------------------------------------
# Slicing / __getitem__ tests
# ---------------------------------------------------------------------------


@pytest.fixture
def six_site_builder():
    """StructureBuilder with 6 Fe sites, each with a distinct charge."""
    sites = [
        {"symbol": "Fe", "position": [0.0, 0.0, float(i)], "charge": float(i)}
        for i in range(6)
    ]
    return StructureBuilder(
        cell=np.eye(3) * 10.0,
        pbc=[True, True, True],
        sites=sites,
    )


@pytest.fixture
def six_site_structure(six_site_builder):
    """Unstored StructureData with the same 6-site layout."""
    return six_site_builder.to_aiida()


def test_len_builder(six_site_builder):
    """len() on a StructureBuilder returns the number of sites."""
    assert len(six_site_builder) == 6


def test_len_structure(six_site_structure):
    """len() on a StructureData returns the number of sites."""
    assert len(six_site_structure) == 6


def test_getitem_int_builder(six_site_builder):
    """Integer index on StructureBuilder returns a one-site StructureBuilder."""
    result = six_site_builder[2]
    assert isinstance(result, StructureBuilder)
    assert len(result) == 1
    assert result.properties.sites[0].charge == 2.0


def test_getitem_int_structure(six_site_structure):
    """Integer index on StructureData returns a one-site StructureData."""
    result = six_site_structure[2]
    assert isinstance(result, StructureData)
    assert len(result) == 1
    assert result.properties.sites[0].charge == 2.0


def test_getitem_negative_index(six_site_builder):
    """Negative integer index selects from the end."""
    result = six_site_builder[-1]
    assert len(result) == 1
    assert result.properties.sites[0].charge == 5.0


def test_getitem_slice(six_site_builder):
    """Slice returns the correct sub-set of sites."""
    result = six_site_builder[1:4]
    assert isinstance(result, StructureBuilder)
    assert len(result) == 3
    charges = [s.charge for s in result.properties.sites]
    assert charges == [1.0, 2.0, 3.0]


def test_getitem_slice_structure(six_site_structure):
    """Slice on StructureData returns a StructureData."""
    result = six_site_structure[0:3]
    assert isinstance(result, StructureData)
    assert len(result) == 3


def test_getitem_stride(six_site_builder):
    """Strided slice selects every other site."""
    result = six_site_builder[::2]
    assert len(result) == 3
    charges = [s.charge for s in result.properties.sites]
    assert charges == [0.0, 2.0, 4.0]


def test_getitem_list(six_site_builder):
    """List index picks an arbitrary, non-contiguous selection."""
    result = six_site_builder[[0, 3, 5]]
    assert isinstance(result, StructureBuilder)
    assert len(result) == 3
    charges = [s.charge for s in result.properties.sites]
    assert charges == [0.0, 3.0, 5.0]


def test_getitem_numpy_array(six_site_builder):
    """1-D numpy integer array works like a list index."""
    idx = np.array([1, 4])
    result = six_site_builder[idx]
    assert len(result) == 2
    charges = [s.charge for s in result.properties.sites]
    assert charges == [1.0, 4.0]


def test_getitem_preserves_cell_and_pbc(six_site_builder):
    """Cell and pbc are preserved unchanged after slicing."""
    result = six_site_builder[0:2]
    assert np.allclose(result.properties.cell, six_site_builder.properties.cell)
    assert list(result.properties.pbc) == list(six_site_builder.properties.pbc)


def test_getitem_out_of_range(six_site_builder):
    """Out-of-range integer index raises IndexError."""
    with pytest.raises(IndexError):
        _ = six_site_builder[10]

    with pytest.raises(IndexError):
        _ = six_site_builder[-7]


def test_getitem_invalid_type(six_site_builder):
    """Unsupported index type raises TypeError."""
    with pytest.raises(TypeError):
        _ = six_site_builder["bad"]


def test_getitem_list_non_int(six_site_builder):
    """List containing a non-integer element raises TypeError."""
    with pytest.raises(TypeError):
        _ = six_site_builder[[0, 1.5]]
