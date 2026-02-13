"""Tests for Site model and related functionality."""
import numpy as np
import pytest
from pydantic import ValidationError

from aiida_atomistic.data.structure.site import Site, FrozenSite, FrozenList


class TestSiteBasic:
    """Test basic Site functionality."""

    def test_site_initialization_minimal(self):
        """Test Site with minimal required fields."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0])

        assert site.symbol == "Cu"
        assert np.allclose(site.position, [0.0, 0.0, 0.0])
        assert site.mass > 0  # Auto-filled from atomic mass
        assert site.charge is None
        assert site.magmom is None

    def test_site_initialization_full(self):
        """Test Site with all fields specified."""
        site = Site(
            symbol="Fe",
            position=[1.0, 2.0, 3.0],
            mass=55.845,
            charge=2.0,
            magmom=[0.0, 0.0, 2.2],
            kind_name="Fe1",
        )

        assert site.symbol == "Fe"
        assert np.allclose(site.position, [1.0, 2.0, 3.0])
        assert site.mass == 55.845
        assert site.charge == 2.0
        assert np.allclose(site.magmom, [0.0, 0.0, 2.2])
        assert site.kind_name == "Fe1"

    def test_site_automatic_mass(self):
        """Test automatic mass assignment."""
        site = Site(symbol="Si", position=[0.0, 0.0, 0.0])
        assert np.isclose(site.mass, 28.0855)

        site = Site(symbol="Au", position=[0.0, 0.0, 0.0])
        assert np.isclose(site.mass, 196.966569)

    def test_site_invalid_symbol(self):
        """Test that invalid symbols raise errors."""
        with pytest.raises(KeyError):
            Site(symbol="Xx", position=[0.0, 0.0, 0.0])

    def test_site_invalid_position(self):
        """Test that invalid positions raise errors."""
        with pytest.raises(ValidationError):
            Site(symbol="Cu", position=[0.0, 0.0])  # Too few dimensions

        with pytest.raises(ValidationError):
            Site(symbol="Cu", position=[0.0, 0.0, 0.0, 0.0])  # Too many dimensions

    def test_site_negative_mass(self):
        """Test that negative mass raises error."""
        with pytest.raises(ValidationError):
            Site(symbol="Cu", position=[0.0, 0.0, 0.0], mass=-1.0)


class TestSiteAlloy:
    """Test alloy functionality in Site."""

    def test_alloy_two_elements(self):
        """Test alloy site with two elements."""
        site = Site(
            symbol=["Cu", "Zn"],  # Use list format
            weight=[0.5, 0.5],
            position=[0.0, 0.0, 0.0],
        )

        assert site.is_alloy
        assert len(site.weight) == 2
        assert sum(site.weight) == pytest.approx(1.0)

    def test_alloy_three_elements(self):
        """Test alloy with three elements."""
        site = Site(
            symbol=["Cu", "Zn", "Ni"],
            position=[0.0, 0.0, 0.0],
            weight=(0.4, 0.4, 0.2),
        )

        assert site.is_alloy
        assert len(site.weight) == 3
        assert sum(site.weight) == pytest.approx(1.0)

    def test_alloy_invalid_weights(self):
        """Test that invalid weights raise errors."""
        with pytest.raises(ValidationError):
            Site(
                symbol=["Cu", "Zn"],
                position=[0.0, 0.0, 0.0],
                weight=(0.5,),  # Wrong number of weights
            )

    def test_alloy_weights_sum_greater_than_one(self):
        """Test that weights > 1 raise error."""
        with pytest.raises(ValidationError):
            Site(
                symbol=["Cu", "Zn"],
                position=[0.0, 0.0, 0.0],
                weight=(0.6, 0.6),  # Sum = 1.2 > 1
            )


class TestSiteVacancy:
    """Test vacancy functionality in Site."""

    def test_vacancy(self):
        """Test site with vacancy."""
        site = Site(
            symbol="Cu",
            position=[0.0, 0.0, 0.0],
            weight=(0.8,),  # 20% vacancy
        )

        assert site.has_vacancies
        assert site.weight == (0.8,)

    def test_no_vacancy(self):
        """Test site without vacancy."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0])

        assert not site.has_vacancies

    def test_alloy_with_vacancy(self):
        """Test alloy with vacancy."""
        site = Site(
            symbol=["Cu", "Zn"],
            position=[0.0, 0.0, 0.0],
            weight=(0.4, 0.3),  # 30% vacancy
        )

        assert site.is_alloy
        assert site.has_vacancies
        assert sum(site.weight) == pytest.approx(0.7)


class TestSiteMagnetic:
    """Test magnetic properties in Site."""

    def test_magmom_vector(self):
        """Test magnetic moment as 3D vector."""
        site = Site(
            symbol="Fe",
            position=[0.0, 0.0, 0.0],
            magmom=[1.0, 2.0, 3.0],
        )

        assert np.allclose(site.magmom, [1.0, 2.0, 3.0])

    def test_magnetization_scalar(self):
        """Test scalar magnetization."""
        site = Site(
            symbol="Fe",
            position=[0.0, 0.0, 0.0],
            magnetization=2.2,
        )

        assert site.magnetization == 2.2
        assert site.magmom is None

    def test_magmom_and_magnetization_exclusive(self):
        """Test that magmom and magnetization are mutually exclusive."""
        with pytest.raises(ValidationError):
            Site(
                symbol="Fe",
                position=[0.0, 0.0, 0.0],
                magmom=[0.0, 0.0, 2.2],
                magnetization=2.2,
            )

    def test_get_magmom_spherical(self):
        """Test conversion to spherical coordinates."""
        site = Site(
            symbol="Fe",
            position=[0.0, 0.0, 0.0],
            magmom=[0.0, 0.0, 2.2],
        )

        spherical = site.get_magmom_coord("spherical")
        assert spherical["starting_magnetization"] == pytest.approx(2.2)
        assert spherical["angle1"] == pytest.approx(0.0)
        assert spherical["angle2"] == pytest.approx(0.0)

    def test_get_magmom_cartesian(self):
        """Test getting magnetic moment in Cartesian coordinates."""
        site = Site(
            symbol="Fe",
            position=[0.0, 0.0, 0.0],
            magmom=[1.0, 2.0, 3.0],
        )

        # Returns dict format
        magmom_cart = site.get_magmom_coord(coord="cartesian")
        assert isinstance(magmom_cart, dict)
        assert "starting_magnetization" in magmom_cart


class TestFrozenSite:
    """Test FrozenSite immutability."""

    def test_frozen_site_creation(self):
        """Test FrozenSite can be created."""
        site = FrozenSite(symbol="Cu", position=[0.0, 0.0, 0.0])

        assert site.symbol == "Cu"
        assert np.allclose(site.position, [0.0, 0.0, 0.0])

    def test_frozen_site_immutability(self):
        """Test FrozenSite cannot be modified."""
        site = FrozenSite(symbol="Cu", position=[0.0, 0.0, 0.0])

        with pytest.raises((ValueError, ValidationError)):
            site.symbol = "Fe"

        with pytest.raises((ValueError, ValidationError)):
            site.charge = 1.0


class TestFrozenList:
    """Test FrozenList functionality."""

    def test_frozen_list_creation(self):
        """Test FrozenList can be created."""
        frozen = FrozenList([1, 2, 3])

        assert len(frozen) == 3
        assert frozen[0] == 1
        assert frozen[2] == 3

    def test_frozen_list_immutability(self):
        """Test FrozenList cannot be modified."""
        frozen = FrozenList([1, 2, 3])

        with pytest.raises(ValueError):
            frozen[0] = 5

        # But reading is fine
        assert frozen[1] == 2

    def test_frozen_list_iteration(self):
        """Test FrozenList can be iterated."""
        frozen = FrozenList([1, 2, 3])

        result = [x * 2 for x in frozen]
        assert result == [2, 4, 6]


class TestSiteConversion:
    """Test Site conversion methods."""

    def test_from_ase_atom(self):
        """Test conversion from ASE Atom."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Cu", position=[1.0, 2.0, 3.0])
        site = Site.from_ase_atom(ase_atom)

        assert site.symbol == "Cu"
        assert np.allclose(site.position, [1.0, 2.0, 3.0])

    def test_from_ase_atom_with_charge(self):
        """Test conversion from ASE Atom with charge."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Cu", position=[0.0, 0.0, 0.0], charge=1.0)
        site = Site.from_ase_atom(ase_atom)

        assert site.charge == 1.0

    def test_from_ase_atom_with_magmom(self):
        """Test conversion from ASE Atom with magnetic moment."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Fe", position=[0.0, 0.0, 0.0], magmom=[0.0, 0.0, 2.2])
        site = Site.from_ase_atom(ase_atom)

        assert np.allclose(site.magmom, [0.0, 0.0, 2.2])

    def test_to_ase(self):
        """Test conversion to ASE Atom."""
        pytest.importorskip("ase")

        site = Site(
            symbol="Cu",
            position=[1.0, 2.0, 3.0],
            charge=1.0,
            kind_name="Cu1",
        )

        ase_atom = site.to_ase()

        assert ase_atom.symbol == "Cu"
        assert np.allclose(ase_atom.position, [1.0, 2.0, 3.0])
        assert ase_atom.charge == 1.0

    def test_site_update(self):
        """Test Site.update() method."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0])

        site.update(charge=1.0, kind_name="Cu1")

        assert site.charge == 1.0
        assert site.kind_name == "Cu1"

    def test_from_ase_atom_with_kwargs_raises(self):
        """Test that passing both aseatom and kwargs raises error."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Cu", position=[0.0, 0.0, 0.0])

        with pytest.raises(ValueError, match="If you pass 'aseatom'"):
            Site.from_ase_atom(ase_atom, charge=1.0)

    def test_from_ase_atom_without_tag_to_kind_name(self):
        """Test conversion from ASE Atom without tag_to_kind_name."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Cu", position=[0.0, 0.0, 0.0], tag=1)
        site = Site.from_ase_atom(ase_atom, tag_to_kind_name=False)

        assert site.symbol == "Cu"
        assert site.kind_name is None or site.kind_name == ""

    def test_from_ase_atom_with_scalar_magmom(self):
        """Test conversion from ASE Atom with scalar magnetization."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Fe", position=[0.0, 0.0, 0.0], magmom=2.2)
        site = Site.from_ase_atom(ase_atom)

        assert site.magmom == 2.2

    def test_from_ase_atom_with_zero_charge(self):
        """Test that zero charge is not set."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Cu", position=[0.0, 0.0, 0.0], charge=0.0)
        site = Site.from_ase_atom(ase_atom)

        assert site.charge is None

    def test_from_ase_atom_with_zero_magmom(self):
        """Test that zero magmom is not set."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Fe", position=[0.0, 0.0, 0.0], magmom=0.0)
        site = Site.from_ase_atom(ase_atom)

        assert site.magnetization is None

    def test_from_ase_atom_with_zero_vector_magmom(self):
        """Test that zero vector magmom is not set."""
        pytest.importorskip("ase")
        from ase import Atom

        ase_atom = Atom("Fe", position=[0.0, 0.0, 0.0], magmom=[0.0, 0.0, 0.0])
        site = Site.from_ase_atom(ase_atom)

        assert site.magmom is None

    def test_from_kwargs_only(self):
        """Test from_ase_atom with kwargs only (no aseatom)."""
        site = Site.from_ase_atom(symbol="Cu", position=[1.0, 2.0, 3.0], charge=1.0)

        assert site.symbol == "Cu"
        assert np.allclose(site.position, [1.0, 2.0, 3.0])
        assert site.charge == 1.0

    def test_to_ase_with_magnetization(self):
        """Test conversion to ASE with magnetization instead of magmom."""
        pytest.importorskip("ase")

        site = Site(
            symbol="Fe",
            position=[0.0, 0.0, 0.0],
            magnetization=2.5,
        )

        ase_atom = site.to_ase()

        assert ase_atom.symbol == "Fe"
        assert ase_atom.magmom == 2.5

    def test_to_ase_with_tag_from_kind_name(self):
        """Test conversion to ASE with tag extracted from kind_name."""
        pytest.importorskip("ase")

        site = Site(
            symbol="Cu",
            position=[0.0, 0.0, 0.0],
            kind_name="Cu2",
        )

        ase_atom = site.to_ase()

        assert ase_atom.tag == 2

    def test_to_ase_with_kind_name_no_tag(self):
        """Test conversion to ASE with kind_name equal to symbol."""
        pytest.importorskip("ase")

        site = Site(
            symbol="Cu",
            position=[0.0, 0.0, 0.0],
            kind_name="Cu",
        )

        ase_atom = site.to_ase()

        assert ase_atom.tag == 0


class TestSiteProperties:
    """Test Site property methods and computed properties."""

    def test_alloy_list_single_element(self):
        """Test alloy_list property for single element."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0])

        # For non-alloy, alloy_list should return list with one element
        alloy_list = site.alloy_list
        assert alloy_list == ["Cu"]

    def test_alloy_list_multiple_elements(self):
        """Test alloy_list property for alloy."""
        site = Site(
            symbol="CuZn",  # String format for alloy
            position=[0.0, 0.0, 0.0],
            weight=(0.5, 0.5),
        )

        alloy_list = site.alloy_list
        assert "Cu" in alloy_list
        assert "Zn" in alloy_list

    def test_has_vacancies_true(self):
        """Test has_vacancies property when sum < 1."""
        site = Site(
            symbol=["Cu", "Zn"],
            position=[0.0, 0.0, 0.0],
            weight=(0.4, 0.4),  # Sum = 0.8 < 1.0
        )

        assert site.has_vacancies is True

    def test_has_vacancies_false(self):
        """Test has_vacancies property when sum = 1."""
        site = Site(
            symbol=["Cu", "Zn"],
            position=[0.0, 0.0, 0.0],
            weight=(0.5, 0.5),  # Sum = 1.0
        )

        assert site.has_vacancies is False

    def test_has_vacancies_none_weight(self):
        """Test has_vacancies returns False when weight is None."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0])

        assert site.has_vacancies is False

    def test_get_default_thresholds(self):
        """Test get_default_thresholds class method."""
        thresholds = Site.get_default_thresholds()

        assert isinstance(thresholds, dict)
        assert "mass" in thresholds
        assert "charge" in thresholds
        assert "magmom" in thresholds

    def test_get_default_values(self):
        """Test get_default_values class method."""
        defaults = Site.get_default_values()

        assert isinstance(defaults, dict)
        assert "mass" in defaults
        assert "charge" in defaults
        assert defaults["charge"] == 0

    def test_get_magmom_coord_none(self):
        """Test get_magmom_coord with None magmom."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0])

        result = site.get_magmom_coord()

        assert result["starting_magnetization"] == 0
        assert result["angle1"] == 0
        assert result["angle2"] == 0

    def test_get_magmom_coord_zero_vector(self):
        """Test get_magmom_coord with zero vector."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magmom=[0.0, 0.0, 0.0])

        result = site.get_magmom_coord()

        assert result["starting_magnetization"] == 0

    def test_get_magmom_coord_spherical(self):
        """Test get_magmom_coord in spherical coordinates."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magmom=[0.0, 0.0, 2.2])

        result = site.get_magmom_coord(coord="spherical")

        assert result["starting_magnetization"] == pytest.approx(2.2)
        assert result["angle1"] == pytest.approx(0.0)  # theta
        assert result["angle2"] == pytest.approx(0.0)  # phi

    def test_get_magmom_coord_cartesian(self):
        """Test get_magmom_coord in cartesian coordinates."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magmom=[1.0, 1.0, 1.0])

        result = site.get_magmom_coord(coord="cartesian")

        assert result["starting_magnetization"] == 1.0
        assert result["angle1"] == 1.0
        assert result["angle2"] == 1.0

    def test_get_magmom_coord_invalid_coord(self):
        """Test get_magmom_coord with invalid coordinate system."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magmom=[0.0, 0.0, 2.2])

        with pytest.raises(ValueError, match="can only be"):
            site.get_magmom_coord(coord="invalid")

    def test_get_magmom_coord_below_threshold(self):
        """Test get_magmom_coord with magnitude below threshold."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magmom=[1e-10, 1e-10, 1e-10])

        result = site.get_magmom_coord(coord="spherical")

        # Should return zeros if below threshold
        assert result["starting_magnetization"] == 0.0


class TestSiteRepr:
    """Test Site string representation."""

    def test_repr_minimal(self):
        """Test __repr__ for minimal site."""
        site = Site(symbol="Cu", position=[1.234, 2.345, 3.456])

        repr_str = repr(site)

        assert "Cu" in repr_str
        assert "1.234" in repr_str or "1.23" in repr_str
        assert "Site(" in repr_str

    def test_repr_with_kind_name(self):
        """Test __repr__ with kind_name different from symbol."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0], kind_name="Cu1")

        repr_str = repr(site)

        assert "kind=Cu1" in repr_str

    def test_repr_with_charge(self):
        """Test __repr__ with charge."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0], charge=1.5)

        repr_str = repr(site)

        assert "charge=1.50" in repr_str

    def test_repr_with_magnetization(self):
        """Test __repr__ with magnetization."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magnetization=2.5)

        repr_str = repr(site)

        assert "magnetization=2.50" in repr_str

    def test_repr_with_magmom(self):
        """Test __repr__ with vector magnetic moment."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magmom=[0.0, 0.0, 2.2])

        repr_str = repr(site)

        assert "magmom=" in repr_str

    def test_repr_alloy(self):
        """Test __repr__ for alloy site."""
        site = Site(
            symbol=["Cu", "Zn"],
            position=[0.0, 0.0, 0.0],
            weight=(0.6, 0.4),
        )

        repr_str = repr(site)

        assert "weight=" in repr_str
        assert "0.60" in repr_str or "0.6" in repr_str


class TestSiteEdgeCases:
    """Test edge cases and special scenarios."""

    def test_site_with_zero_mass_uses_default(self):
        """Test that zero mass is replaced with atomic mass."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0], mass=0)

        assert site.mass > 0
        assert site.mass == pytest.approx(63.546)

    def test_both_magmom_and_magnetization_raises(self):
        """Test that specifying both magmom and magnetization raises error."""
        with pytest.raises(ValueError, match="You can specify only one"):
            Site(
                symbol="Fe",
                position=[0.0, 0.0, 0.0],
                magmom=[0.0, 0.0, 2.2],
                magnetization=2.5,
            )

    def test_alloy_without_weight_raises(self):
        """Test that alloy without weight raises error."""
        with pytest.raises(ValueError, match="weight"):
            Site(
                symbol=["Cu", "Zn"],
                position=[0.0, 0.0, 0.0],
            )

    def test_position_frozen_after_creation(self):
        """Test that position array is frozen after site creation."""
        site = Site(symbol="Cu", position=[0.0, 0.0, 0.0])

        # Position should be non-writable
        with pytest.raises((ValueError, AttributeError)):
            site.position[0] = 1.0

    def test_magmom_frozen_after_creation(self):
        """Test that magmom array is frozen after site creation."""
        site = Site(symbol="Fe", position=[0.0, 0.0, 0.0], magmom=[0.0, 0.0, 2.2])

        # Magmom should be non-writable
        with pytest.raises((ValueError, AttributeError)):
            site.magmom[0] = 1.0
