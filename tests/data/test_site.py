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
