"""Tests for property getter methods in StructureData and StructureBuilder."""

import json
import numpy as np
import pytest

from aiida_atomistic.data.structure import StructureBuilder, StructureData


# ============================================================================
# BASIC PROPERTY GETTERS
# ============================================================================


class TestBasicPropertyGetters:
    """Test basic property access (cell, pbc, positions, etc.)."""

    def test_get_cell(self):
        """Test accessing cell property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        assert np.allclose(
            structure.properties.cell, [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]]
        )

        # Test with StructureData
        structure_data = StructureData(
            cell=[[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Cu", "position": [0, 0, 0]}],
        )
        assert np.allclose(
            structure_data.properties.cell, [[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]]
        )

    def test_get_pbc(self):
        """Test accessing pbc property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, False, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        assert structure.properties.pbc == [True, False, True]

        # Test with all True
        structure_3d = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert all(structure_3d.properties.pbc)

    def test_get_positions(self):
        """Test accessing positions property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        positions = structure.properties.positions
        assert np.allclose(positions, [[0, 0, 0], [1.5, 1.5, 1.5]])

    def test_get_charges(self):
        """Test accessing charges property."""
        # Without charges
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert structure.properties.charges is None

        # With charges
        structure_charged = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ],
        )
        assert np.allclose(structure_charged.properties.charges, [2.0, -2.0])

    def test_get_magmoms(self):
        """Test accessing magmoms property."""
        # Without magmoms
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert structure.properties.magmoms is None

        # With magmoms
        structure_magnetic = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magmom": [0, 0, -2.2]},
            ],
        )
        assert np.allclose(
            structure_magnetic.properties.magmoms, [[0, 0, 2.2], [0, 0, -2.2]]
        )

    def test_get_magnetizations(self):
        """Test accessing magnetizations property."""
        # Without magnetizations
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert structure.properties.magnetizations is None

        # With magnetizations
        structure_magnetic = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magnetization": 2.5},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magnetization": -2.5},
            ],
        )
        assert np.allclose(structure_magnetic.properties.magnetizations, [2.5, -2.5])

    def test_get_masses(self):
        """Test accessing masses property."""
        # Default masses (from symbols)
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        masses = structure.properties.masses
        assert masses is not None
        assert len(masses) == 2

        # Custom masses
        structure_custom = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "mass": 56.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "mass": 16.0},
            ],
        )
        assert np.allclose(structure_custom.properties.masses, [56.0, 16.0])

    def test_get_symbols(self):
        """Test accessing symbols property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        symbols = structure.properties.symbols
        assert symbols == ["Fe", "O"]

    def test_get_weights(self):
        """Test accessing weights property for alloy sites."""
        # Non-alloy structure
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        weights = structure.properties.weights
        assert weights is None or all(w is None for w in weights)

        # Alloy structure
        structure_alloy = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": ["Fe", "Ni"], "position": [0, 0, 0], "weight": [0.7, 0.3]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        weights = structure_alloy.properties.weights
        assert np.allclose(weights[0], [0.7, 0.3])


class TestRedundantPropertyAccessors:
    """Test redundant property accessors (lines 54-78) - for backwards compatibility."""

    def test_property_sites(self):
        """Test sites property accessor."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert len(structure.sites) == 1
        assert structure.sites[0].symbol == "Fe"

    def test_property_kinds(self):
        """Test kinds property accessor."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1"}],
        )
        kinds = structure.to_kinds()
        assert len(kinds.properties.kinds) > 0

    def test_property_is_alloy(self):
        """Test is_alloy property accessor."""
        # Pure structure
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert not structure.is_alloy

    def test_property_has_vacancies(self):
        """Test has_vacancies property accessor."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert not structure.has_vacancies

    def test_property_formula(self):
        """Test formula property accessor."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        assert "Fe" in structure.formula
        assert "O" in structure.formula


# ============================================================================
# COMPUTED PROPERTY GETTERS
# ============================================================================


class TestComputedPropertyGetters:
    """Test accessing computed properties."""

    def test_get_cell_volume(self):
        """Test accessing cell_volume computed property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        volume = structure.properties.cell_volume
        assert volume == pytest.approx(27.0, rel=1e-6)

    def test_get_dimensionality(self):
        """Test accessing dimensionality computed property."""
        # 3D structure
        structure_3d = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        dim = structure_3d.properties.dimensionality
        assert dim["dim"] == 3
        assert dim["label"] == "volume"

        # 2D structure
        structure_2d = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 20.0]],
            pbc=[True, True, False],
            sites=[{"symbol": "C", "position": [0, 0, 0]}],
        )
        dim = structure_2d.properties.dimensionality
        assert dim["dim"] == 2

    def test_get_formula(self):
        """Test accessing formula computed property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        formula = structure.properties.formula
        assert "Fe" in formula
        assert "O" in formula


# ============================================================================
# GETTER METHODS
# ============================================================================


class TestMethodGetters:
    """Test getter methods (get_kind, get_composition, etc.)."""

    def test_get_defined_properties_default(self):
        """Test get_defined_properties() with default parameters."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ],
        )

        defined = structure.get_defined_properties()

        # Should include site arrays with singular_form
        assert "charges" in defined
        assert "positions" in defined
        assert "symbols" in defined

        # Should exclude computed without singular_form (default behavior)
        assert "formula" not in defined
        assert "cell_volume" not in defined

    def test_get_defined_properties_exclude_computed(self):
        """Test get_defined_properties() with exclude_computed=True."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ],
        )

        defined = structure.get_defined_properties(exclude_computed=True)

        # Should exclude all computed fields
        assert "charges" not in defined
        assert "positions" not in defined
        assert "formula" not in defined
        assert "cell_volume" not in defined

        # Should include only base fields
        assert "cell" in defined
        assert "pbc" in defined
        assert "sites" in defined

    def test_get_defined_properties_include_computed_without_singular(self):
        """Test get_defined_properties() with exclude_computed_without_singular=False."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ],
        )

        defined = structure.get_defined_properties(
            exclude_computed_without_singular=False
        )

        # Should include all computed fields
        assert "charges" in defined
        assert "positions" in defined
        assert "composition" in defined
        assert "cell_volume" in defined

    def test_get_defined_properties_no_charges(self):
        """Test get_defined_properties() when charges are not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        defined = structure.get_defined_properties()

        # Charges should not be in defined properties
        assert "charges" not in defined

        # But positions should be
        assert "positions" in defined

    def test_get_defined_properties_with_magmoms(self):
        """Test get_defined_properties() with magnetic moments."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magmom": [0, 0, -2.2]},
            ],
        )

        defined = structure.get_defined_properties()
        assert "magmoms" in defined

    def test_get_defined_properties_immutable(self):
        """Test get_defined_properties() with StructureData (immutable)."""
        structure = StructureData(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        defined = structure.get_defined_properties()

        # Should include charges (only first site has it, but property is defined)
        assert "charges" in defined
        assert "positions" in defined

    def test_get_supported_properties(self):
        """Test get_supported_properties() class method."""
        supported_builder = StructureBuilder.get_supported_properties()
        supported_data = StructureData.get_supported_properties()

        # Should return dict with 'global' and 'site' keys
        assert isinstance(supported_builder, dict)
        assert isinstance(supported_data, dict)
        assert "global" in supported_builder
        assert "site" in supported_builder
        assert "global" in supported_data
        assert "site" in supported_data

        # Should include common properties
        for prop in ["cell", "pbc", "sites"]:
            assert prop in supported_builder["global"]
            assert prop in supported_data["global"]

        for prop in ["charge", "magmom", "mass", "position", "symbol"]:
            assert prop in supported_builder["site"]
            assert prop in supported_data["site"]

    def test_get_computed_properties(self):
        """Test get_computed_properties() class method."""
        computed_builder = StructureBuilder.get_computed_properties()
        computed_data = StructureData.get_computed_properties()

        # Should return set of computed property names
        assert isinstance(computed_builder, set)
        assert isinstance(computed_data, set)

        # Should include computed properties
        for prop in [
            "composition",
            "cell_volume",
            "dimensionality",
            "positions",
            "charges",
            "magmoms",
        ]:
            assert prop in computed_builder
            assert prop in computed_data

    def test_get_kind_names(self):
        """Test get_kind_names() method."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1"},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "kind_name": "Fe2"},
                {"symbol": "O", "position": [1.5, 0, 0], "kind_name": "O1"},
            ],
        )

        kind_names = structure.get_kind_names()
        assert kind_names is not None
        assert len(kind_names) == 3
        assert "Fe1" in kind_names
        assert "Fe2" in kind_names
        assert "O1" in kind_names

    def test_get_kind(self):
        """Test get_kind() method."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {
                    "symbol": "Fe",
                    "position": [0, 0, 0],
                    "kind_name": "Fe1",
                    "charge": 2.0,
                },
                {
                    "symbol": "Fe",
                    "position": [1.5, 1.5, 1.5],
                    "kind_name": "Fe2",
                    "charge": 3.0,
                },
            ],
        )

        kind_fe1 = structure.get_kind("Fe1")
        assert kind_fe1 is not None
        # Kind should contain information about the site with that kind_name

        kind_fe2 = structure.get_kind("Fe2")
        assert kind_fe2 is not None

    def test_get_composition(self):
        """Test get_composition() method."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
                {"symbol": "O", "position": [0, 1.5, 1.5]},
            ],
        )

        composition = structure.get_composition()
        assert composition is not None
        assert "Fe" in composition
        assert "O" in composition

    def test_get_description(self):
        """Test get_description() method."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        description = structure.get_description()
        assert isinstance(description, str)
        assert len(description) > 0

    def test_get_symbols_set(self):
        """Test get_symbols_set() method."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
                {"symbol": "Fe", "position": [0, 1.5, 1.5]},
            ],
        )

        symbols_set = structure.get_symbols_set()
        assert isinstance(symbols_set, set)
        assert "Fe" in symbols_set
        assert "O" in symbols_set
        assert len(symbols_set) == 2

    def test_get_pymatgen_structure(self):
        """Test get_pymatgen_structure() method."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        pmg_structure = structure.get_pymatgen_structure()
        assert pmg_structure is not None
        from pymatgen.core import Structure

        assert isinstance(pmg_structure, Structure)
        assert len(pmg_structure) == 2

    def test_get_pymatgen_molecule(self):
        """Test get_pymatgen_molecule() method for molecular structures."""
        structure = StructureBuilder(
            cell=[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
            pbc=[False, False, False],
            sites=[
                {"symbol": "H", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.0, 0, 0]},
                {"symbol": "H", "position": [1.5, 0.5, 0]},
            ],
        )

        pmg_molecule = structure.get_pymatgen_molecule()
        assert pmg_molecule is not None
        from pymatgen.core import Molecule

        assert isinstance(pmg_molecule, Molecule)
        assert len(pmg_molecule) == 3


class TestKindRelatedGetters:
    """Test get_kind and is_collinear methods (lines 159-174)."""

    def test_get_kind_existing(self):
        """Test get_kind with existing kind name."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1"}],
        )
        kinds_structure = structure.to_kinds()
        kind = kinds_structure.get_kind("Fe1")
        assert kind is not None
        assert kind.kind_name == "Fe1"

    def test_get_kind_nonexistent(self):
        """Test get_kind with non-existent kind name."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        kinds_structure = structure.to_kinds()
        kind = kinds_structure.get_kind("NonExistent")
        assert kind is None

    def test_is_collinear_no_magmoms(self):
        """Test is_collinear when no magmoms are defined."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert not structure.is_collinear

    def test_is_collinear_with_magnetizations(self):
        """Test is_collinear when magnetizations are provided (collinear case)."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magnetization": 2.0},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magnetization": -2.0},
            ],
        )
        assert structure.is_collinear

    def test_is_collinear_with_parallel_magmoms(self):
        """Test is_collinear with parallel magnetic moments."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magmom": [0, 0, -1.0]},
            ],
        )
        # Should be collinear since all magmoms are parallel (along z-axis)
        assert structure.is_collinear


class TestFromASE:
    """Test from_ase method (lines 183-207)."""

    def test_from_ase_basic(self):
        """Test from_ase with a basic ASE Atoms object."""
        try:
            from ase import Atoms

            ase_atoms = Atoms(
                "H2O",
                positions=[[0, 0, 0], [0, 0, 1], [0, 1, 0]],
                cell=[5, 5, 5],
                pbc=True,
            )

            structure = StructureBuilder.from_ase(ase_atoms)
            assert len(structure.properties.sites) == 3
            assert np.allclose(
                structure.properties.cell, [[5, 0, 0], [0, 5, 0], [0, 0, 5]]
            )
        except ImportError:
            pytest.skip("ASE not available")

    def test_from_ase_with_tags(self):
        """Test from_ase with tags (creates kind names from tags)."""
        try:
            from ase import Atoms

            ase_atoms = Atoms(
                "Fe2", positions=[[0, 0, 0], [1.5, 1.5, 1.5]], cell=[3, 3, 3], pbc=True
            )
            ase_atoms.set_tags([1, 2])

            structure = StructureBuilder.from_ase(ase_atoms)
            assert len(structure.properties.sites) == 2
        except ImportError:
            pytest.skip("ASE not available")


class TestFromFile:
    """Test from_file method (lines 221-229)."""

    def test_from_file_regular_format(self, tmp_path):
        """Test from_file with regular format (e.g., xyz)."""
        try:
            from ase import Atoms
            import ase.io as ase_io

            # Create a test XYZ file
            xyz_file = tmp_path / "test.xyz"
            atoms = Atoms("H2", positions=[[0, 0, 0], [0, 0, 1]], cell=[5, 5, 5])
            ase_io.write(str(xyz_file), atoms, format="xyz")

            structure = StructureBuilder.from_file(str(xyz_file), format="xyz")
            assert len(structure.properties.sites) == 2
        except ImportError:
            pytest.skip("ASE not available")


class TestFromPymatgen:
    """Test from_pymatgen and related methods (lines 242-386)."""

    def test_from_pymatgen_molecule(self):
        """Test from_pymatgen with a Molecule object."""
        try:
            from pymatgen.core import Molecule

            mol = Molecule(["H", "H"], [[0, 0, 0], [0, 0, 1]])

            structure = StructureBuilder.from_pymatgen(mol)
            assert len(structure.properties.sites) == 2
            assert structure.properties.pbc == [False, False, False]
        except ImportError:
            pytest.skip("Pymatgen not available")

    def test_from_pymatgen_structure(self):
        """Test from_pymatgen with a Structure object."""
        try:
            from pymatgen.core import Structure, Lattice

            lattice = Lattice([[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]])
            structure_pmg = Structure(
                lattice, ["Fe", "O"], [[0, 0, 0], [0.5, 0.5, 0.5]]
            )

            structure = StructureBuilder.from_pymatgen(structure_pmg)
            assert len(structure.properties.sites) == 2
            assert structure.properties.pbc == [True, True, True]
        except ImportError:
            pytest.skip("Pymatgen not available")


class TestValidateKinds:
    """Test validate_kinds method (lines 396-413)."""

    def test_validate_kinds_no_kinds(self):
        """Test validate_kinds when no kinds are defined."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        with pytest.raises(ValueError, match="No kinds defined"):
            structure.validate_kinds()

    def test_validate_kinds_valid(self):
        """Test validate_kinds with valid kinds."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        kinds_structure = structure.to_kinds()
        # Should not raise
        assert kinds_structure.validate_kinds()


class TestToKinds:
    """Test to_kinds method (lines 427-440)."""

    def test_to_kinds_builder(self):
        """Test to_kinds on StructureBuilder."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        kinds_structure = structure.to_kinds()
        assert len(kinds_structure.properties.kinds) > 0

    def test_to_kinds_with_threshold(self):
        """Test to_kinds with custom threshold."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "charge": 2.01},
            ],
        )
        kinds_structure = structure.to_kinds(threshold={"charge": 0.1})
        # With large threshold, should group both Fe atoms
        assert len(kinds_structure.properties.kinds) == 1


class TestToDict:
    """Test to_dict method (lines 451-454)."""

    def test_to_dict_basic(self):
        """Test to_dict returns proper dictionary."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        dict_repr = structure.to_dict()
        assert "cell" in dict_repr
        assert "pbc" in dict_repr
        assert "sites" in dict_repr

    def test_to_dict_excludes_computed(self):
        """Test that to_dict excludes computed fields."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        dict_repr = structure.to_dict()
        # Computed fields like formula should not be in dict
        assert "formula" not in dict_repr


class TestToCIF:
    """Test to_cif method (lines 464-474)."""

    def test_to_cif_invalid_converter(self):
        """Test to_cif with invalid converter raises ValueError."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        with pytest.raises(ValueError, match="No such converter"):
            structure.to_cif(converter="invalid_converter")


class TestGetCompositionModes:
    """Test get_composition method with different modes (lines 507-519)."""

    def test_get_composition_reduced(self):
        """Test get_composition with reduced mode."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        comp = structure.get_composition(mode="reduced")
        assert comp["Fe"] == 2
        assert comp["O"] == 1

    def test_get_composition_fractional(self):
        """Test get_composition with fractional mode."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        comp = structure.get_composition(mode="fractional")
        assert comp["Fe"] == 0.5
        assert comp["O"] == 0.5

    def test_get_composition_invalid_mode(self):
        """Test get_composition with invalid mode."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        with pytest.raises(ValueError, match="mode .* is invalid"):
            structure.get_composition(mode="invalid")


class TestToASE:
    """Test to_ase method (lines 534-537)."""

    def test_to_ase_basic(self):
        """Test to_ase conversion."""
        try:
            structure = StructureBuilder(
                cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
                pbc=[True, True, True],
                sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            )
            ase_atoms = structure.to_ase()
            assert len(ase_atoms) == 1
            assert ase_atoms.get_chemical_symbols()[0] == "Fe"
        except ImportError:
            pytest.skip("ASE not available")


class TestToPymatgen:
    """Test to_pymatgen method (lines 554-557)."""

    def test_to_pymatgen_structure(self):
        """Test to_pymatgen for 3D structure."""
        try:
            structure = StructureBuilder(
                cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
                pbc=[True, True, True],
                sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            )
            pmg_structure = structure.to_pymatgen()
            assert len(pmg_structure) == 1
        except ImportError:
            pytest.skip("Pymatgen not available")

    def test_to_pymatgen_molecule(self):
        """Test to_pymatgen for molecule (no PBC)."""
        try:
            structure = StructureBuilder(
                cell=[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
                pbc=[False, False, False],
                sites=[
                    {"symbol": "H", "position": [5, 5, 5]},
                    {"symbol": "H", "position": [5, 5, 6]},
                ],
            )
            pmg_mol = structure.to_pymatgen()
            assert len(pmg_mol) == 2
        except ImportError:
            pytest.skip("Pymatgen not available")


class TestToFile:
    """Test to_file method (lines 570-579)."""

    def test_to_file_no_filename(self):
        """Test to_file without filename raises ValueError."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        with pytest.raises(ValueError, match="provide a valid filename"):
            structure.to_file(filename=None)

    def test_to_file_cif(self, tmp_path):
        """Test to_file with CIF format."""
        try:
            structure = StructureBuilder(
                cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
                pbc=[True, True, True],
                sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            )
            output_file = tmp_path / "test.cif"
            structure.to_file(filename=str(output_file), format="cif")
            assert output_file.exists()
        except ImportError:
            pytest.skip("ASE not available")


# ============================================================================
# FORMAT PREPARATION METHODS
# ============================================================================


class TestPrepareXSF:
    """Test _prepare_xsf method (lines 630-650)."""

    def test_prepare_xsf_basic(self):
        """Test _prepare_xsf for basic structure."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        xsf_bytes, metadata = structure._prepare_xsf()
        xsf_str = xsf_bytes.decode("utf-8")
        assert "CRYSTAL" in xsf_str
        assert "PRIMVEC" in xsf_str
        assert "PRIMCOORD" in xsf_str


class TestPrepareCIF:
    """Test _prepare_cif method (lines 654-657)."""

    def test_prepare_cif_basic(self):
        """Test _prepare_cif conversion."""
        try:
            structure = StructureBuilder(
                cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
                pbc=[True, True, True],
                sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            )
            cif_bytes, metadata = structure._prepare_cif()
            assert isinstance(cif_bytes, bytes)
        except ImportError:
            pytest.skip("ASE/CifData not available")


class TestPrepareChemDoodle:
    """Test _prepare_chemdoodle method (lines 661-728)."""

    def test_prepare_chemdoodle_basic(self):
        """Test _prepare_chemdoodle JSON generation."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        json_bytes, metadata = structure._prepare_chemdoodle()
        json_str = json_bytes.decode("utf-8")
        data = json.loads(json_str)
        assert "m" in data
        assert "s" in data
        assert data["units"] == "&Aring;"


class TestPrepareXYZ:
    """Test _prepare_xyz method (lines 732-770)."""

    def test_prepare_xyz_basic(self):
        """Test _prepare_xyz for basic structure."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, False],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        xyz_bytes, metadata = structure._prepare_xyz()
        xyz_str = xyz_bytes.decode("utf-8")
        assert "2" in xyz_str  # Number of atoms
        assert "Lattice=" in xyz_str
        assert "pbc=" in xyz_str
        assert "Fe" in xyz_str
        assert "O" in xyz_str


# ============================================================================
# INTERNAL CONVERSION METHODS
# ============================================================================


class TestGetObjectASE:
    """Test _get_object_ase method (lines 858-870)."""

    def test_get_object_ase_basic(self):
        """Test _get_object_ase conversion."""
        try:
            structure = StructureBuilder(
                cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
                pbc=[True, True, True],
                sites=[
                    {"symbol": "Fe", "position": [0, 0, 0]},
                    {"symbol": "O", "position": [1.5, 1.5, 1.5]},
                ],
            )
            ase_atoms = structure._get_object_ase()
            assert len(ase_atoms) == 2
            assert np.allclose(
                ase_atoms.get_cell(), [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]]
            )
        except ImportError:
            pytest.skip("ASE not available")


class TestGetObjectPymatgenRouting:
    """Test _get_object_pymatgen routing method (lines 883-886)."""

    def test_get_object_pymatgen_routes_to_structure(self):
        """Test that _get_object_pymatgen routes to structure for periodic systems."""
        try:
            structure = StructureBuilder(
                cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
                pbc=[True, True, True],
                sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            )
            result = structure._get_object_pymatgen()
            # Should be Structure, not Molecule
            from pymatgen.core import Structure

            assert isinstance(result, Structure)
        except ImportError:
            pytest.skip("Pymatgen not available")

    def test_get_object_pymatgen_routes_to_molecule(self):
        """Test that _get_object_pymatgen routes to molecule for non-periodic systems."""
        try:
            structure = StructureBuilder(
                cell=[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
                pbc=[False, False, False],
                sites=[
                    {"symbol": "H", "position": [5, 5, 5]},
                    {"symbol": "H", "position": [5, 5, 6]},
                ],
            )
            result = structure._get_object_pymatgen()
            # Should be Molecule, not Structure
            from pymatgen.core import Molecule

            assert isinstance(result, Molecule)
        except ImportError:
            pytest.skip("Pymatgen not available")


# ============================================================================
# DIMENSIONALITY METHODS
# ============================================================================


class TestGetDimensionality:
    """Test _get_dimensionality method (lines 1046-1073)."""

    def test_get_dimensionality_0d(self):
        """Test dimensionality for 0D structure."""
        structure = StructureBuilder(
            cell=[[10.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
            pbc=[False, False, False],
            sites=[{"symbol": "H", "position": [5, 5, 5]}],
        )
        dim = structure._get_dimensionality()
        assert dim["dim"] == 0
        assert dim["value"] == 0

    def test_get_dimensionality_1d(self):
        """Test dimensionality for 1D structure."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 10.0, 0], [0, 0, 10.0]],
            pbc=[True, False, False],
            sites=[{"symbol": "C", "position": [0, 5, 5]}],
        )
        dim = structure._get_dimensionality()
        assert dim["dim"] == 1
        assert dim["value"] > 0

    def test_get_dimensionality_2d(self):
        """Test dimensionality for 2D structure."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 10.0]],
            pbc=[True, True, False],
            sites=[{"symbol": "C", "position": [0, 0, 5]}],
        )
        dim = structure._get_dimensionality()
        assert dim["dim"] == 2
        assert dim["value"] > 0

    def test_get_dimensionality_3d(self):
        """Test dimensionality for 3D structure."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        dim = structure._get_dimensionality()
        assert dim["dim"] == 3
        assert dim["value"] > 0


class TestValidateDimensionality:
    """Test _validate_dimensionality method (lines 1079-1091)."""

    def test_validate_dimensionality_0d(self):
        """Test validation for 0D structure (no constraints)."""
        structure = StructureBuilder(
            cell=[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            pbc=[False, False, False],
            sites=[{"symbol": "H", "position": [0, 0, 0]}],
        )
        # Should not raise
        structure._validate_dimensionality()

    def test_validate_dimensionality_zero_volume_error(self):
        """Test validation raises error for finite-d structure with zero volume."""
        structure = StructureBuilder(
            cell=[[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        with pytest.raises(ValueError, match="but.*-d volume 0"):
            structure._validate_dimensionality()


class TestGetSymbolsSetMethod:
    """Test get_symbols_set method (line 1100)."""

    def test_get_symbols_set_single(self):
        """Test get_symbols_set with single element."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        symbols = structure.get_symbols_set()
        assert symbols == {"Fe"}

    def test_get_symbols_set_multiple(self):
        """Test get_symbols_set with multiple elements."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
                {"symbol": "Fe", "position": [1.5, 0, 0]},
            ],
        )
        symbols = structure.get_symbols_set()
        assert isinstance(symbols, set)
        assert symbols == {"Fe", "O"}


# ============================================================================
# SITE PROPERTY GETTERS
# ============================================================================


class TestSitePropertyGetters:
    """Test accessing properties of individual sites."""

    def test_get_site_charge(self):
        """Test accessing charge of individual sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ],
        )

        assert structure.properties.sites[0].charge == 2.0
        assert structure.properties.sites[1].charge == -2.0

    def test_get_site_magmom(self):
        """Test accessing magmom of individual sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magmom": [0, 0, -2.2]},
            ],
        )

        assert np.allclose(structure.properties.sites[0].magmom, [0, 0, 2.2])
        assert np.allclose(structure.properties.sites[1].magmom, [0, 0, -2.2])

    def test_get_site_mass(self):
        """Test accessing mass of individual sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "mass": 56.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "mass": 16.0},
            ],
        )

        assert structure.properties.sites[0].mass == 56.0
        assert structure.properties.sites[1].mass == 16.0

    def test_get_site_position(self):
        """Test accessing position of individual sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        assert np.allclose(structure.properties.sites[0].position, [0, 0, 0])
        assert np.allclose(structure.properties.sites[1].position, [1.5, 1.5, 1.5])

    def test_get_site_symbol(self):
        """Test accessing symbol of individual sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        assert structure.properties.sites[0].symbol == "Fe"
        assert structure.properties.sites[1].symbol == "O"

    def test_get_site_kind_name(self):
        """Test accessing kind_name of individual sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1"},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "kind_name": "Fe2"},
            ],
        )

        assert structure.properties.sites[0].kind_name == "Fe1"
        assert structure.properties.sites[1].kind_name == "Fe2"

    def test_get_site_weight(self):
        """Test accessing weight of alloy sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": ["Fe", "Ni"], "position": [0, 0, 0], "weight": [0.7, 0.3]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        assert np.allclose(structure.properties.sites[0].weight, [0.7, 0.3])
        assert structure.properties.sites[1].weight is None


# ============================================================================
# CUSTOM PROPERTY GETTERS
# ============================================================================


class TestCustomPropertyGetters:
    """Test accessing custom properties."""

    def test_get_custom_properties(self):
        """Test accessing custom properties dictionary."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            custom={"temperature": 300.0, "pressure": 1.0},
        )

        assert structure.properties.custom is not None
        assert "temperature" in structure.properties.custom
        assert structure.properties.custom["temperature"] == 300.0
        assert "pressure" in structure.properties.custom
        assert structure.properties.custom["pressure"] == 1.0

    def test_get_custom_properties_none(self):
        """Test that custom is None when not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        # Custom should be None if not provided
        assert structure.properties.custom is None or structure.properties.custom == {}


# ============================================================================
# GLOBAL PROPERTY GETTERS
# ============================================================================


class TestGlobalPropertyGetters:
    """Test accessing global properties (tot_charge, tot_magnetization)."""

    def test_get_tot_charge(self):
        """Test accessing tot_charge property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            tot_charge=2.0,
        )

        assert structure.properties.tot_charge == 2.0

    def test_get_tot_charge_none(self):
        """Test that tot_charge is None when not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        assert structure.properties.tot_charge is None

    def test_get_tot_magnetization(self):
        """Test accessing tot_magnetization property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            tot_magnetization=2.5,
        )

        assert structure.properties.tot_magnetization == 2.5

    def test_get_tot_magnetization_none(self):
        """Test that tot_magnetization is None when not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        assert structure.properties.tot_magnetization is None


# === 11. ADDITIONAL EDGE CASES FOR COVERAGE ===


class TestLenMethod:
    """Test __len__ method."""

    def test_len_structure(self):
        """Test that len() returns the number of sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )
        assert len(structure) == 2


class TestFromFileMCIF:
    """Test from_file with MCIF format."""

    def test_from_file_mcif(self):
        """Test from_file with .mcif extension (uses pymatgen parser)."""
        try:
            import tempfile
            import os

            # Create a simple mcif content
            mcif_content = """data_test
_cell_length_a 5.0
_cell_length_b 5.0
_cell_length_c 5.0
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M 'P 1'
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Fe1 Fe 0.0 0.0 0.0
"""
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mcif", delete=False
            ) as f:
                f.write(mcif_content)
                temp_path = f.name

            try:
                structure = StructureBuilder.from_file(temp_path)
                assert len(structure.properties.sites) >= 1
            finally:
                os.unlink(temp_path)
        except ImportError:
            pytest.skip("Pymatgen not available")


class TestToCIFConverter:
    """Test to_cif with invalid converter."""

    def test_to_cif_invalid_converter(self):
        """Test to_cif raises ValueError for invalid converter."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        with pytest.raises(ValueError, match="No such converter.*available"):
            structure.to_cif(converter="invalid_converter")


class TestGetCompositionInvalidMode:
    """Test get_composition with invalid mode."""

    def test_get_composition_invalid_mode(self):
        """Test that get_composition raises ValueError for invalid mode."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Ba", "position": [0, 0, 0]},
                {"symbol": "Ti", "position": [1.5, 1.5, 1.5]},
            ],
        )
        with pytest.raises(ValueError, match="mode.*invalid"):
            structure.get_composition(mode="invalid_mode")


class TestPrepareXSFWithAlloy:
    """Test _prepare_xsf error handling for alloys."""

    def test_prepare_xsf_alloy_raises(self):
        """Test that _prepare_xsf raises NotImplementedError for alloys."""
        # Create a structure that triggers is_alloy (multiple symbols with weights)
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": ["Fe", "Co"], "position": [0, 0, 0], "weight": [0.5, 0.5]},
            ],
        )
        # Verify it's recognized as an alloy
        assert structure.is_alloy
        with pytest.raises(NotImplementedError, match="XSF for alloys"):
            structure._prepare_xsf()


class TestGetObjectPhonopyAtoms:
    """Test _get_object_phonopyatoms conversion."""

    def test_get_object_phonopyatoms(self):
        """Test conversion to PhonopyAtoms object."""
        try:
            from phonopy.structure.atoms import PhonopyAtoms

            structure = StructureBuilder(
                cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
                pbc=[True, True, True],
                sites=[
                    {"symbol": "Fe", "position": [0, 0, 0], "mass": 55.845},
                ],
            )

            phonopy_atoms = structure._get_object_phonopyatoms()
            assert isinstance(phonopy_atoms, PhonopyAtoms)
            assert len(phonopy_atoms) == 1
        except ImportError:
            pytest.skip("Phonopy not available")


class TestDimensionalityValidationError:
    """Test dimensionality validation error path."""

    def test_validate_dimensionality_singular_cell_error(self):
        """Test validation raises error for periodic structure with singular cell."""
        structure = StructureBuilder(
            cell=[[5.0, 0, 0], [0, 0, 0], [0, 0, 0]],  # Singular in 2 dimensions
            pbc=[True, True, True],  # But claiming 3D periodicity
            sites=[{"symbol": "H", "position": [0, 0, 0]}],
        )
        with pytest.raises(ValueError, match="but.*-d volume 0"):
            structure._validate_dimensionality()
