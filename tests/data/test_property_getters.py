"""Tests for property getter methods in StructureData and StructureBuilder."""
import numpy as np
import pytest

from aiida_atomistic.data.structure import StructureBuilder, StructureData


class TestBasicPropertyGetters:
    """Test basic property access (cell, pbc, positions, etc.)."""

    def test_get_cell(self):
        """Test accessing cell property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )

        assert np.allclose(structure.properties.cell, [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]])

        # Test with StructureData
        structure_data = StructureData(
            cell=[[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Cu", "position": [0, 0, 0]}]
        )
        assert np.allclose(structure_data.properties.cell, [[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]])

    def test_get_pbc(self):
        """Test accessing pbc property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, False, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )

        assert structure.properties.pbc == [True, False, True]

        # Test with all True
        structure_3d = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
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
            ]
        )

        positions = structure.properties.positions
        assert np.allclose(positions, [[0, 0, 0], [1.5, 1.5, 1.5]])

    def test_get_charges(self):
        """Test accessing charges property."""
        # Without charges
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )
        assert structure.properties.charges is None

        # With charges
        structure_charged = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ]
        )
        assert np.allclose(structure_charged.properties.charges, [2.0, -2.0])

    def test_get_magmoms(self):
        """Test accessing magmoms property."""
        # Without magmoms
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )
        assert structure.properties.magmoms is None

        # With magmoms
        structure_magnetic = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magmom": [0, 0, -2.2]},
            ]
        )
        assert np.allclose(structure_magnetic.properties.magmoms, [[0, 0, 2.2], [0, 0, -2.2]])

    def test_get_magnetizations(self):
        """Test accessing magnetizations property."""
        # Without magnetizations
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )
        assert structure.properties.magnetizations is None

        # With magnetizations
        structure_magnetic = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magnetization": 2.5},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magnetization": -2.5},
            ]
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
            ]
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
            ]
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
            ]
        )

        symbols = structure.properties.symbols
        assert symbols == ["Fe", "O"]

    def test_get_weights(self):
        """Test accessing weights property for alloy sites."""
        # Non-alloy structure
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
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
            ]
        )
        weights = structure_alloy.properties.weights
        assert np.allclose(weights[0], [0.7, 0.3])


class TestComputedPropertyGetters:
    """Test accessing computed properties."""

    def test_get_cell_volume(self):
        """Test accessing cell_volume computed property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )

        volume = structure.properties.cell_volume
        assert volume == pytest.approx(27.0, rel=1e-6)

    def test_get_dimensionality(self):
        """Test accessing dimensionality computed property."""
        # 3D structure
        structure_3d = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )
        dim = structure_3d.properties.dimensionality
        assert dim['dim'] == 3
        assert dim['label'] == 'volume'

        # 2D structure
        structure_2d = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 20.0]],
            pbc=[True, True, False],
            sites=[{"symbol": "C", "position": [0, 0, 0]}]
        )
        dim = structure_2d.properties.dimensionality
        assert dim['dim'] == 2

    def test_get_formula(self):
        """Test accessing formula computed property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        formula = structure.properties.formula
        assert "Fe" in formula
        assert "O" in formula


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
            ]
        )

        defined = structure.get_defined_properties()

        # Should include site arrays with singular_form
        assert 'charges' in defined
        assert 'positions' in defined
        assert 'symbols' in defined

        # Should exclude computed without singular_form (default behavior)
        assert 'formula' not in defined
        assert 'cell_volume' not in defined

    def test_get_defined_properties_exclude_computed(self):
        """Test get_defined_properties() with exclude_computed=True."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ]
        )

        defined = structure.get_defined_properties(exclude_computed=True)

        # Should exclude all computed fields
        assert 'charges' not in defined
        assert 'positions' not in defined
        assert 'formula' not in defined
        assert 'cell_volume' not in defined

        # Should include only base fields
        assert 'cell' in defined
        assert 'pbc' in defined
        assert 'sites' in defined

    def test_get_defined_properties_include_computed_without_singular(self):
        """Test get_defined_properties() with exclude_computed_without_singular=False."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ]
        )

        defined = structure.get_defined_properties(exclude_computed_without_singular=False)

        # Should include all computed fields
        assert 'charges' in defined
        assert 'positions' in defined
        assert 'formula' in defined
        assert 'cell_volume' in defined

    def test_get_defined_properties_no_charges(self):
        """Test get_defined_properties() when charges are not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )

        defined = structure.get_defined_properties()

        # Charges should not be in defined properties
        assert 'charges' not in defined

        # But positions should be
        assert 'positions' in defined

    def test_get_defined_properties_with_magmoms(self):
        """Test get_defined_properties() with magnetic moments."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magmom": [0, 0, -2.2]},
            ]
        )

        defined = structure.get_defined_properties()
        assert 'magmoms' in defined

    def test_get_defined_properties_immutable(self):
        """Test get_defined_properties() with StructureData (immutable)."""
        structure = StructureData(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        defined = structure.get_defined_properties()

        # Should include charges (only first site has it, but property is defined)
        assert 'charges' in defined
        assert 'positions' in defined

    def test_get_supported_properties(self):
        """Test get_supported_properties() class method."""
        supported_builder = StructureBuilder.get_supported_properties()
        supported_data = StructureData.get_supported_properties()

        # Should return list of property names
        assert isinstance(supported_builder, list)
        assert isinstance(supported_data, list)

        # Should include common properties
        for prop in ['cell', 'pbc', 'sites', 'charges', 'magmoms', 'masses']:
            assert prop in supported_builder
            assert prop in supported_data

    def test_get_computed_properties(self):
        """Test get_computed_properties() class method."""
        computed_builder = StructureBuilder.get_computed_properties()
        computed_data = StructureData.get_computed_properties()

        # Should return list of computed property names
        assert isinstance(computed_builder, list)
        assert isinstance(computed_data, list)

        # Should include computed properties
        for prop in ['formula', 'cell_volume', 'dimensionality', 'positions', 'charges', 'magmoms']:
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
            ]
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
                {"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1", "charge": 2.0},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "kind_name": "Fe2", "charge": 3.0},
            ]
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
            ]
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
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
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
            ]
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
            ]
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
            ]
        )

        pmg_molecule = structure.get_pymatgen_molecule()
        assert pmg_molecule is not None
        from pymatgen.core import Molecule
        assert isinstance(pmg_molecule, Molecule)
        assert len(pmg_molecule) == 3


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
            ]
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
            ]
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
            ]
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
            ]
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
            ]
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
            ]
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
            ]
        )

        assert np.allclose(structure.properties.sites[0].weight, [0.7, 0.3])
        assert structure.properties.sites[1].weight is None


class TestCustomPropertyGetters:
    """Test accessing custom properties."""

    def test_get_custom_properties(self):
        """Test accessing custom properties dictionary."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            custom={'temperature': 300.0, 'pressure': 1.0}
        )

        assert structure.properties.custom is not None
        assert 'temperature' in structure.properties.custom
        assert structure.properties.custom['temperature'] == 300.0
        assert 'pressure' in structure.properties.custom
        assert structure.properties.custom['pressure'] == 1.0

    def test_get_custom_properties_none(self):
        """Test that custom is None when not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )

        # Custom should be None if not provided
        assert structure.properties.custom is None or structure.properties.custom == {}


class TestGlobalPropertyGetters:
    """Test accessing global properties (tot_charge, tot_magnetization)."""

    def test_get_tot_charge(self):
        """Test accessing tot_charge property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            tot_charge=2.0
        )

        assert structure.properties.tot_charge == 2.0

    def test_get_tot_charge_none(self):
        """Test that tot_charge is None when not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )

        assert structure.properties.tot_charge is None

    def test_get_tot_magnetization(self):
        """Test accessing tot_magnetization property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            tot_magnetization=2.5
        )

        assert structure.properties.tot_magnetization == 2.5

    def test_get_tot_magnetization_none(self):
        """Test that tot_magnetization is None when not set."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}]
        )

        assert structure.properties.tot_magnetization is None
