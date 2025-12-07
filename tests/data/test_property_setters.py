"""Tests for property setter and remover methods in StructureBuilder."""
import numpy as np
import pytest

from aiida_atomistic.data.structure import StructureBuilder, StructureData


class TestPropertySetters:
    """Test setter methods for structure properties."""

    def test_set_charges(self):
        """Test setting charges for all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Set charges
        structure.set_charges([2.0, -2.0])

        assert np.allclose(structure.properties.charges, [2.0, -2.0])
        assert structure.properties.sites[0].charge == 2.0
        assert structure.properties.sites[1].charge == -2.0

    def test_set_charges_length_mismatch(self):
        """Test that setting charges with wrong length raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        with pytest.raises(ValueError):
            structure.set_charges([2.0])  # Only 1 charge for 2 sites

    def test_set_magmoms(self):
        """Test setting magnetic moments for all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Set magmoms
        structure.set_magmoms([[0, 0, 2.2], [0, 0, -2.2]])

        assert np.allclose(structure.properties.magmoms, [[0, 0, 2.2], [0, 0, -2.2]])
        assert np.allclose(structure.properties.sites[0].magmom, [0, 0, 2.2])
        assert np.allclose(structure.properties.sites[1].magmom, [0, 0, -2.2])

    def test_set_magnetizations(self):
        """Test setting scalar magnetizations for all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Set magnetizations
        structure.set_magnetizations([2.5, -2.5])

        assert np.allclose(structure.properties.magnetizations, [2.5, -2.5])
        assert structure.properties.sites[0].magnetization == 2.5
        assert structure.properties.sites[1].magnetization == -2.5

    def test_set_masses(self):
        """Test setting masses for all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Set custom masses
        structure.set_masses([56.0, 16.0])

        assert np.allclose(structure.properties.masses, [56.0, 16.0])
        assert structure.properties.sites[0].mass == 56.0
        assert structure.properties.sites[1].mass == 16.0

    def test_set_weights(self):
        """Test setting weights for alloy sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": ["Fe", "Ni"], "position": [0, 0, 0], "weight": [0.5, 0.5]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Set weights
        structure.set_weights([[0.7, 0.3], None])

        assert np.allclose(structure.properties.sites[0].weight, [0.7, 0.3])
        assert structure.properties.sites[1].weight is None


class TestPropertyRemovers:
    """Test remover methods for structure properties."""

    def test_remove_charges(self):
        """Test removing charges from all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ]
        )

        # Verify charges are set
        assert structure.properties.charges is not None
        assert np.allclose(structure.properties.charges, [2.0, -2.0])

        # Remove charges
        structure.remove_charges()

        # Verify charges are removed
        assert structure.properties.charges is None
        assert structure.properties.sites[0].charge is None
        assert structure.properties.sites[1].charge is None

    def test_remove_magmoms(self):
        """Test removing magnetic moments from all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magmom": [0, 0, -2.2]},
            ]
        )

        # Verify magmoms are set
        assert structure.properties.magmoms is not None

        # Remove magmoms
        structure.remove_magmoms()

        # Verify magmoms are removed
        assert structure.properties.magmoms is None
        assert structure.properties.sites[0].magmom is None
        assert structure.properties.sites[1].magmom is None

    def test_remove_magnetizations(self):
        """Test removing scalar magnetizations from all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magnetization": 2.5},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "magnetization": -2.5},
            ]
        )

        # Verify magnetizations are set
        assert structure.properties.magnetizations is not None

        # Remove magnetizations
        structure.remove_magnetizations()

        # Verify magnetizations are removed
        assert structure.properties.magnetizations is None
        assert structure.properties.sites[0].magnetization is None
        assert structure.properties.sites[1].magnetization is None

    def test_remove_masses(self):
        """Test removing custom masses from all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "mass": 56.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "mass": 16.0},
            ]
        )

        # Verify masses are set
        assert structure.properties.masses is not None

        # Remove masses (will revert to default atomic masses)
        structure.remove_masses()

        # Verify masses are reset to defaults
        # After removal, masses should be auto-calculated from symbols
        assert structure.properties.sites[0].mass is None
        assert structure.properties.sites[1].mass is None

    def test_remove_weights(self):
        """Test removing weights from alloy sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": ["Fe", "Ni"], "position": [0, 0, 0], "weight": [0.7, 0.3]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Verify weights are set
        assert structure.properties.sites[0].weight is not None

        # Remove weights
        structure.remove_weights()

        # Verify weights are removed
        assert structure.properties.sites[0].weight is None
        assert structure.properties.sites[1].weight is None

    def test_remove_tot_charge(self):
        """Test removing total charge."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            tot_charge=2.0
        )

        # Verify tot_charge is set
        assert structure.properties.tot_charge == 2.0

        # Remove tot_charge
        structure.remove_tot_charge()

        # Verify tot_charge is removed
        assert structure.properties.tot_charge is None

    def test_remove_property_generic(self):
        """Test generic remove_property method."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ]
        )

        # Verify charges are set
        assert structure.properties.charges is not None

        # Remove using generic method
        structure.remove_property("charge")

        # Verify charges are removed
        assert structure.properties.charges is None
        assert structure.properties.sites[0].charge is None
        assert structure.properties.sites[1].charge is None

class TestSetterRemoverWorkflow:
    """Test combined workflows of setting and removing properties."""

    def test_set_then_remove_charges(self):
        """Test setting charges and then removing them."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Initially no charges
        assert structure.properties.charges is None

        # Set charges
        structure.set_charges([2.0, -2.0])
        assert np.allclose(structure.properties.charges, [2.0, -2.0])

        # Remove charges
        structure.remove_charges()
        assert structure.properties.charges is None

    def test_modify_multiple_properties(self):
        """Test setting and removing multiple properties."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5]},
            ]
        )

        # Set multiple properties
        structure.set_charges([2.0, 2.0])
        structure.set_magmoms([[0, 0, 2.2], [0, 0, -2.2]])
        structure.set_masses([56.0, 56.0])

        assert np.allclose(structure.properties.charges, [2.0, 2.0])
        assert structure.properties.magmoms is not None
        assert structure.properties.masses is not None

        # Remove charges only
        structure.remove_charges()
        assert structure.properties.charges is None
        assert structure.properties.magmoms is not None  # Still there
        assert structure.properties.masses is not None  # Still there

        # Remove magmoms
        structure.remove_magmoms()
        assert structure.properties.magmoms is None
        assert structure.properties.masses is not None  # Still there

    def test_convert_to_immutable_after_remove(self):
        """Test that structure can be converted to immutable after removing properties."""
        mutable = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ]
        )

        # Remove charges
        mutable.remove_charges()

        # Convert to immutable
        immutable = StructureData(**mutable.to_dict())

        # Verify charges are not present
        assert immutable.properties.charges is None
        assert 'charges' not in immutable.get_defined_properties()

class TestCustomPropertySettersRemovers:
    """Test setter and remover methods for custom properties in StructureBuilder."""

    def test_set_then_remove_charges(self):
        """Test setting charges and then removing them."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
            custom = {'first_custom_property': 'Hello'}
        )


        # Initially only one custom property
        assert structure.properties.custom == {'first_custom_property': 'Hello'}
        ## testing also for StructureData
        structuredata = structure.to_aiida()
        assert structuredata.properties.custom == {'first_custom_property': 'Hello'}

        # Set another property
        structure.set_custom({'second_custom_property': "World"})
        assert structure.properties.custom == {'first_custom_property': 'Hello', 'second_custom_property': 'World'}

        # Remove custom properties: first only one, then the whole dictionary
        structure.remove_custom(['first_custom_property'])
        assert structure.properties.custom == {'second_custom_property': 'World'}

        structure.remove_custom()
        assert structure.properties.custom is None
