"""Tests for property setter and remover methods in StructureBuilder.

This module contains comprehensive tests organized into logical sections:
1. BASIC PROPERTY SETTERS - Testing setter methods for various properties
2. PROPERTY REMOVERS - Testing remover methods for all properties
3. SITE MANIPULATION TESTS - Testing site manipulation methods (update, append, pop, clear) and edge cases
4. INTEGRATION AND WORKFLOW TESTS - Testing combined workflows and real-world usage patterns
"""

import numpy as np
import pytest

from aiida_atomistic.data.structure import StructureBuilder, StructureData


# ============================================================================
# BASIC PROPERTY SETTERS
# ============================================================================


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
            ],
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
            ],
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
            ],
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
            ],
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
            ],
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
            ],
        )

        # Set weights
        structure.set_weights([[0.7, 0.3], None])

        assert np.allclose(structure.properties.sites[0].weight, [0.7, 0.3])
        assert structure.properties.sites[1].weight is None


# ============================================================================
# PROPERTY REMOVERS
# ============================================================================


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
            ],
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
            ],
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
            ],
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
            ],
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
            ],
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
            tot_charge=2.0,
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
            ],
        )

        # Verify charges are set
        assert structure.properties.charges is not None

        # Remove using generic method
        structure.remove_property("charge")

        # Verify charges are removed
        assert structure.properties.charges is None
        assert structure.properties.sites[0].charge is None
        assert structure.properties.sites[1].charge is None


# ============================================================================
# SITE MANIPULATION TESTS
# ============================================================================


class TestSetterEdgeCases:
    """Test edge cases and error handling in setter methods."""

    def test_set_then_remove_charges(self):
        """Test setting charges and then removing them."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
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
            ],
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
            ],
        )

        # Remove charges
        mutable.remove_charges()

        # Convert to immutable
        immutable = StructureData(**mutable.to_dict())

        # Verify charges are not present
        assert immutable.properties.charges is None
        assert "charges" not in immutable.get_defined_properties()


# ============================================================================
# INTEGRATION AND WORKFLOW TESTS
# ============================================================================


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
            ],
            custom={"first_custom_property": "Hello"},
        )

        # Initially only one custom property
        assert structure.properties.custom == {"first_custom_property": "Hello"}
        ## testing also for StructureData
        structuredata = structure.to_aiida()
        assert structuredata.properties.custom == {"first_custom_property": "Hello"}

        # Set another property
        structure.set_custom({"second_custom_property": "World"})
        assert structure.properties.custom == {
            "first_custom_property": "Hello",
            "second_custom_property": "World",
        }

        # Remove custom properties: first only one, then the whole dictionary
        structure.remove_custom(["first_custom_property"])
        assert structure.properties.custom == {"second_custom_property": "World"}

        structure.remove_custom()
        assert structure.properties.custom is None


class TestSetterEdgeCases2:
    """Test edge cases and error handling in setter methods."""

    def test_set_cell_lengths_not_implemented(self):
        """Test that set_cell_lengths raises NotImplementedError."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        with pytest.raises(NotImplementedError):
            structure.set_cell_lengths([4.0, 4.0, 4.0])

    def test_set_cell_angles_not_implemented(self):
        """Test that set_cell_angles raises NotImplementedError."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        with pytest.raises(NotImplementedError):
            structure.set_cell_angles([90, 90, 90])

    def test_update_sites_single_index(self):
        """Test updating a single site by index."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        # Update single site
        structure.update_sites(0, charge=2.0, magmom=[0, 0, 2.5])

        assert structure.properties.sites[0].charge == 2.0
        assert np.allclose(structure.properties.sites[0].magmom, [0, 0, 2.5])
        assert structure.properties.sites[1].charge is None  # Unchanged

    def test_update_sites_list_of_indices(self):
        """Test updating multiple sites by list of indices."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        # Update multiple sites
        structure.update_sites([0, 1], charge=2.0)

        assert structure.properties.sites[0].charge == 2.0
        assert structure.properties.sites[1].charge == 2.0
        assert structure.properties.sites[2].charge is None  # Unchanged

    def test_update_kind(self):
        """Test updating all sites with a specific kind_name."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1"},
                {"symbol": "Fe", "position": [1.5, 0, 0], "kind_name": "Fe1"},
                {"symbol": "Fe", "position": [0, 1.5, 0], "kind_name": "Fe2"},
            ],
        )

        # Update all Fe1 sites
        structure.update_kind("Fe1", charge=2.0)

        assert structure.properties.sites[0].charge == 2.0
        assert structure.properties.sites[1].charge == 2.0
        assert structure.properties.sites[2].charge is None  # Different kind

    def test_update_kind_no_kinds_defined(self):
        """Test that update_kind raises error when no kinds are defined."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        with pytest.raises(
            ValueError,
            match="You cannot update a kind if the structure has no kinds defined",
        ):
            structure.update_kind("Fe1", charge=2.0)

    def test_append_atom_with_kwargs(self):
        """Test appending atom using kwargs."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        structure.append_atom(symbol="O", position=[1.5, 1.5, 1.5], charge=-2.0)

        assert len(structure.properties.sites) == 2
        assert structure.properties.sites[1].symbol == "O"
        assert structure.properties.sites[1].charge == -2.0

    def test_append_atom_no_params_raises_error(self):
        """Test that append_atom without params raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        with pytest.raises(
            ValueError,
            match="Must provide either 'atom' parameter or keyword arguments",
        ):
            structure.append_atom()

    def test_append_atom_dict_with_kwargs_raises_error(self):
        """Test that providing both dict and kwargs raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        with pytest.raises(
            ValueError, match="Cannot provide both 'atom' as dict and keyword arguments"
        ):
            structure.append_atom(
                {"symbol": "O", "position": [1.5, 1.5, 1.5]}, charge=-2.0
            )

    def test_append_atom_site_with_kwargs_raises_error(self):
        """Test that providing both Site and kwargs raises error."""
        from aiida_atomistic.data.structure.site import Site

        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        site = Site(symbol="O", position=[1.5, 1.5, 1.5])

        with pytest.raises(
            ValueError, match="Cannot provide both 'atom' as Site and keyword arguments"
        ):
            structure.append_atom(site, charge=-2.0)

    def test_append_atom_invalid_type_raises_error(self):
        """Test that append_atom with invalid type raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        with pytest.raises(TypeError, match="atom must be Site, dict, or None"):
            structure.append_atom("invalid")

    def test_append_atom_same_position_raises_error(self):
        """Test that appending atom at same position raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        with pytest.raises(
            ValueError,
            match="You cannot define two different sites to be in the same position",
        ):
            structure.append_atom(symbol="O", position=[0, 0, 0])

    def test_append_atom_at_specific_index(self):
        """Test appending atom at specific index."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        structure.append_atom(symbol="Cu", position=[0.5, 0.5, 0.5], index=1)

        assert len(structure.properties.sites) == 3
        assert structure.properties.sites[1].symbol == "Cu"
        assert structure.properties.sites[2].symbol == "O"

    def test_append_atom_index_out_of_range(self):
        """Test that invalid index raises IndexError."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        with pytest.raises(IndexError, match="index .* out of range"):
            structure.append_atom(symbol="O", position=[1.5, 1.5, 1.5], index=10)

    def test_append_atom_to_empty_structure(self):
        """Test appending atom to empty structure."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[],
        )

        structure.append_atom(symbol="Fe", position=[0, 0, 0])

        assert len(structure.properties.sites) == 1
        assert structure.properties.sites[0].symbol == "Fe"

    def test_pop_atom_default(self):
        """Test popping last atom."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        structure.pop_atom()

        assert len(structure.properties.sites) == 1
        assert structure.properties.sites[0].symbol == "Fe"

    def test_pop_atom_specific_index(self):
        """Test popping atom at specific index."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
                {"symbol": "Cu", "position": [2.5, 2.5, 2.5]},
            ],
        )

        structure.pop_atom(1)

        assert len(structure.properties.sites) == 2
        assert structure.properties.sites[0].symbol == "Fe"
        assert structure.properties.sites[1].symbol == "Cu"

    def test_clear_sites(self):
        """Test clearing all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -2.0},
            ],
        )

        structure.clear_sites()

        assert len(structure.properties.sites) == 0
        assert structure.properties.cell is not None  # Cell still there
        assert structure.properties.pbc is not None  # PBC still there

    def test_set_magmoms_length_mismatch(self):
        """Test that setting magmoms with wrong length raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5]},
            ],
        )

        with pytest.raises(ValueError, match="The length of the magmoms list"):
            structure.set_magmoms([[0, 0, 2.2]])  # Only 1 magmom for 2 sites

    def test_set_magnetizations_length_mismatch(self):
        """Test that setting magnetizations with wrong length raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5]},
            ],
        )

        with pytest.raises(ValueError, match="The length of the magnetizations array"):
            structure.set_magnetizations([2.5])  # Only 1 value for 2 sites

    def test_set_masses_length_mismatch(self):
        """Test that setting masses with wrong length raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        with pytest.raises(ValueError, match="The length of the masses list"):
            structure.set_masses([56.0])  # Only 1 mass for 2 sites

    def test_set_weights_length_mismatch(self):
        """Test that setting weights with wrong length raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": ["Fe", "Ni"], "position": [0, 0, 0], "weight": [0.5, 0.5]},
                {"symbol": "O", "position": [1.5, 1.5, 1.5]},
            ],
        )

        with pytest.raises(ValueError, match="The length of the weights array"):
            structure.set_weights([[0.7, 0.3]])  # Only 1 weight for 2 sites

    def test_set_tot_charge(self):
        """Test setting total charge."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        structure.set_tot_charge(2.5)

        assert structure.properties.tot_charge == 2.5

    def test_set_tot_magnetization(self):
        """Test setting total magnetization."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        structure.set_tot_magnetization(4.5)

        assert structure.properties.tot_magnetization == 4.5

    def test_remove_hubbard(self):
        """Test removing hubbard property."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        # Set hubbard to some value
        structure.properties.hubbard = "some_value"

        # Remove hubbard
        structure.remove_hubbard()

        assert structure.properties.hubbard is None

    def test_set_kind_names(self):
        """Test setting kind_names for all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5]},
            ],
        )

        structure.set_kind_names(["Fe1", "Fe2"])

        assert structure.properties.sites[0].kind_name == "Fe1"
        assert structure.properties.sites[1].kind_name == "Fe2"

    def test_set_kind_names_length_mismatch(self):
        """Test that setting kind_names with wrong length raises error."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5]},
            ],
        )

        with pytest.raises(ValueError, match="The length of the kind_names list"):
            structure.set_kind_names(["Fe1"])  # Only 1 name for 2 sites

    def test_remove_kind_names(self):
        """Test removing kind_names from all sites."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "kind_name": "Fe1"},
                {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "kind_name": "Fe2"},
            ],
        )

        structure.remove_kind_names()

        assert structure.properties.sites[0].kind_name is None
        assert structure.properties.sites[1].kind_name is None

    def test_set_custom_new_dict(self):
        """Test setting custom properties on structure without existing custom dict."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        assert structure.properties.custom is None

        structure.set_custom({"my_property": "value"})

        assert structure.properties.custom == {"my_property": "value"}

    def test_remove_custom_no_dict(self):
        """Test removing custom properties when none exist."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        # Should not raise error
        structure.remove_custom()
        assert structure.properties.custom is None

    def test_remove_custom_specific_keys_not_exist(self):
        """Test removing custom properties with keys that don't exist."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            custom={"prop1": "value1"},
        )

        # Should not raise error for non-existent keys
        structure.remove_custom(["prop2", "prop3"])
        assert structure.properties.custom == {"prop1": "value1"}

    def test_set_pbc(self):
        """Test setting PBC."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        structure.set_pbc([False, False, True])

        assert structure.properties.pbc == [False, False, True]

    def test_set_cell(self):
        """Test setting cell."""
        structure = StructureBuilder(
            cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
            pbc=[True, True, True],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )

        new_cell = [[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]]
        structure.set_cell(new_cell)

        assert np.allclose(structure.properties.cell, new_cell)
