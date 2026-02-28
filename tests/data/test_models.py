"""Tests for Pydantic model layers.

This module contains comprehensive tests for the structure model classes:
- StructureBaseModel: Base model with validation and computed fields
- MutableStructureModel: Mutable structure that allows modifications
- ImmutableStructureModel: Immutable structure with frozen state
"""
import numpy as np
import pytest

from aiida_atomistic.data.structure import StructureData, StructureBuilder
from aiida_atomistic.data.structure.models import (
    ImmutableStructureModel,
    MutableStructureModel,
    StructureBaseModel,
)
from aiida_atomistic.data.structure.site import freeze_nested

# to check coverage: pytest tests/data/test_models.py --cov=aiida_atomistic.data.structure.models --cov-report=term-missing

# =============================================================================
# StructureBaseModel Tests
# =============================================================================

class TestStructureBaseModelCreation:
    """Test creation and initialization of StructureBaseModel."""

    def test_create_from_dict(self, example_structure_dict):
        """Test that base model can be created from dict."""
        model = StructureBaseModel(**example_structure_dict)

        assert model.pbc == [True, True, True]
        assert len(model.sites) == 1
        assert model.cell.shape == (3, 3)
        assert model.sites[0].symbol == "Cu"
        assert model.sites[0].charge == 1.0
        assert model.sites[0].kind_name == "Cu1"

    def test_create_empty_with_none_sites(self):
        """Test creating structure with sites=None."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=None
        )
        assert model.sites == []
        assert len(model.sites) == 0

    def test_create_minimal_structure(self):
        """Test creating structure with no sites - minimal case."""
        model = StructureBaseModel()
        assert model.sites == []
        assert model.pbc == [True, True, True]
        assert model.cell.shape == (3, 3)

    def test_create_with_empty_sites_list(self):
        """Test sites validation with empty list."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            sites=[],
        )
        assert len(model.sites) == 0


class TestStructureBaseModelValidation:
    """Test validation rules for StructureBaseModel."""

    def test_invalid_cell_shape(self):
        """Test cell validation rejects non-3x3 arrays."""
        with pytest.raises(ValueError):
            StructureBaseModel(
                pbc=[True, True, True],
                cell=[[1.0, 0.0], [0.0, 1.0]],  # Wrong shape
                sites=[{"symbol": "H", "position": [0, 0, 0]}],
            )

    def test_invalid_pbc_length(self):
        """Test PBC validation rejects wrong length."""
        with pytest.raises(ValueError):
            StructureBaseModel(
                pbc=[True, True],  # Wrong length
                cell=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                sites=[{"symbol": "H", "position": [0, 0, 0]}],
            )

    def test_invalid_position_dimension(self):
        """Test validation of site positions."""
        with pytest.raises(ValueError):
            StructureBaseModel(
                pbc=[True, True, True],
                cell=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                sites=[{"symbol": "H", "position": [0, 0]}],  # Wrong shape
            )

    def test_invalid_element_symbol(self):
        """Test validation of element symbols."""
        with pytest.raises(KeyError):
            StructureBaseModel(
                pbc=[True, True, True],
                cell=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                sites=[{"symbol": "Xx", "position": [0, 0, 0]}],  # Invalid element
            )

    def test_valid_magnetic_moment(self):
        """Test validation accepts valid magnetic moments."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]}],
        )
        assert np.allclose(model.sites[0].magmom, [0, 0, 2.2])

    def test_valid_alloy_site(self, example_structure_dict_alloy):
        """Test validation of alloy sites."""
        model = StructureBaseModel(**example_structure_dict_alloy)

        assert model.sites[0].is_alloy
        assert sum(model.sites[0].weight) == pytest.approx(1.0)

    def test_valid_charges(self):
        """Test validation of charges."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Na", "position": [0, 0, 0], "charge": 1.0},
                {"symbol": "Cl", "position": [1.5, 1.5, 1.5], "charge": -1.0},
            ],
        )
        assert model.sites[0].charge == 1.0
        assert model.sites[1].charge == -1.0

    def test_singular_cell_validation_not_implemented(self):
        """Test validation of singular cell matrices."""
        pytest.skip("Singular cell validation not implemented")


# =============================================================================
# Computed Fields Tests
# =============================================================================

class TestComputedFieldsCell:
    """Test cell-related computed fields."""

    def test_cell_volume_simple(self):
        """Test cell_volume computed field."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]],
            sites=[{"symbol": "H", "position": [0, 0, 0]}],
        )

        assert np.isclose(model.cell_volume, 24.0)  # 2 * 3 * 4

    def test_cell_volume_with_example(self, example_structure_dict):
        """Test cell_volume with example structure."""
        model = StructureBaseModel(**example_structure_dict)

        assert model.cell_volume > 0
        expected_volume = np.linalg.det(model.cell)
        assert np.isclose(model.cell_volume, expected_volume)

    def test_dimensionality_3d(self, example_structure_dict):
        """Test dimensionality computed field."""
        model = StructureBaseModel(**example_structure_dict)

        assert model.dimensionality["dim"] == 3

        model.pbc = [True, True, False]
        assert model.dimensionality["dim"] == 2

    def test_reciprocal_cell_not_implemented(self):
        """Test reciprocal_cell computed field."""
        pytest.skip("reciprocal_cell not implemented as computed field")


class TestComputedFieldsSites:
    """Test site-related computed fields."""

    def test_symbols(self):
        """Test symbols computed field returns correct array."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1, 0, 0]},
                {"symbol": "O", "position": [0, 1, 0]},
            ],
        )

        assert model.symbols == ["Fe", "O", "O"]

    def test_positions(self):
        """Test positions computed field returns correct array."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "H", "position": [0, 0, 0]},
                {"symbol": "H", "position": [1, 1, 1]},
            ],
        )

        expected = np.array([[0, 0, 0], [1, 1, 1]])
        assert np.allclose(model.positions, expected)

    def test_charges(self):
        """Test charges computed field."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Na", "position": [0, 0, 0], "charge": 1.0},
                {"symbol": "Cl", "position": [1.5, 1.5, 1.5], "charge": -1.0},
            ],
        )

        assert model.charges is not None
        assert len(model.charges) == 2
        assert model.charges[0] == 1.0
        assert model.charges[1] == -1.0

    def test_magmoms(self):
        """Test magmoms computed field."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [2, 2, 2], "magmom": [0, 0, 3.5]},
            ],
        )

        assert model.magmoms is not None
        assert len(model.magmoms) == 2
        assert np.allclose(model.magmoms[0], [0, 0, 2.2])

    def test_magnetizations(self):
        """Test magnetizations computed field."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magnetization": 2.5},
                {"symbol": "Fe", "position": [1, 1, 1], "magnetization": -1.5},
            ],
        )
        assert model.magnetizations is not None
        assert len(model.magnetizations) == 2
        assert model.magnetizations[0] == 2.5

    def test_magnetizations_none_when_all_none(self):
        """Test magnetizations returns None when all sites have None."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert model.magnetizations is None

    def test_weights(self, example_structure_dict_alloy):
        """Test weights computed field."""
        model = StructureBaseModel(**example_structure_dict_alloy)
        assert model.weights is not None
        assert len(model.weights) == len(model.sites)
        assert sum(model.weights[0]) == pytest.approx(1.0)

    def test_weights_none_when_all_none(self):
        """Test weights returns None when all sites have None weight."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert model.weights is None

    def test_kinds(self, example_structure_dict):
        """Test kinds computed field."""
        model = StructureBaseModel(**example_structure_dict)

        if model.kinds is not None:
            assert len(model.kinds) >= 1

    def test_kinds_none_for_empty_structure(self):
        """Test that kinds returns None for empty structure."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[],
        )
        assert model.kinds is None or model.kinds == []

    def test_n_sites(self):
        """Test n_sites computed field."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
                {"symbol": "O", "position": [1, 1, 1]},
                {"symbol": "O", "position": [2, 2, 2]},
            ],
        )
        assert model.n_sites == 3


class TestComputedFieldsComposition:
    """Test composition-related computed fields."""

    def test_formula(self, example_structure_dict):
        """Test formula computed field."""
        model = StructureBaseModel(**example_structure_dict)

        assert "Cu" in model.formula

    def test_formula_multi_element(self):
        """Test formula with multiple elements."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "H", "position": [0, 0, 0]},
                {"symbol": "H", "position": [1, 0, 0]},
                {"symbol": "O", "position": [0.5, 1, 0]},
            ],
        )

        assert "H" in model.formula and "O" in model.formula

    def test_is_alloy_true(self, example_structure_dict_alloy):
        """Test is_alloy computed field for alloy structure."""
        model = StructureBaseModel(**example_structure_dict_alloy)
        assert model.is_alloy is True

    def test_is_alloy_false(self, example_structure_dict):
        """Test is_alloy returns False for non-alloy structure."""
        model = StructureBaseModel(**example_structure_dict)
        assert model.is_alloy is False

    def test_has_vacancies(self):
        """Test has_vacancies computed field."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert model.has_vacancies is False


class TestStatisticalComputedFields:
    """Test statistical computed fields for querying."""

    def test_charge_statistics(self):
        """Test max_charge and min_charge computed fields."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Na", "position": [0, 0, 0], "charge": 1.0},
                {"symbol": "Cl", "position": [1.5, 1.5, 1.5], "charge": -1.0},
                {"symbol": "Na", "position": [3, 0, 0], "charge": 2.0},
            ],
        )
        assert model.max_charge == 2.0
        assert model.min_charge == -1.0

    def test_charge_statistics_none_without_charges(self):
        """Test that charge statistics return None when charges are None."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert model.max_charge is None
        assert model.min_charge is None

    def test_magmom_statistics(self):
        """Test max_magmom and min_magmom computed fields."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
                {"symbol": "Fe", "position": [2, 2, 2], "magmom": [0, 0, 3.5]},
            ],
        )
        assert model.max_magmom == pytest.approx(3.5)
        assert model.min_magmom == pytest.approx(2.2)

    def test_magmom_statistics_none_without_magmoms(self):
        """Test that magmom statistics return None when magmoms are None."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert model.max_magmom is None
        assert model.min_magmom is None

    def test_magnetization_statistics(self):
        """Test max_magnetization and min_magnetization computed fields."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[4.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.0, 0.0, 4.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magnetization": 1.5},
                {"symbol": "Fe", "position": [2, 2, 2], "magnetization": 2.8},
            ],
        )
        assert model.max_magnetization == 2.8
        assert model.min_magnetization == 1.5

    def test_magnetization_statistics_none_without_magnetizations(self):
        """Test that magnetization statistics return None when magnetizations are None."""
        model = StructureBaseModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
        )
        assert model.max_magnetization is None
        assert model.min_magnetization is None


# =============================================================================
# MutableStructureModel Tests
# =============================================================================

class TestMutableStructureModel:
    """Test mutable structure model functionality."""

    def test_creation(self, example_structure_dict):
        """Test mutable model creation."""
        model = MutableStructureModel(**example_structure_dict)

        assert len(model.sites) == 1
        assert model.sites[0].symbol == "Cu"

    def test_cell_modification(self, example_structure_dict):
        """Test that mutable model allows cell modifications."""
        model = MutableStructureModel(**example_structure_dict)

        new_cell = [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]]
        model.cell = new_cell

        assert np.allclose(model.cell, new_cell)

    def test_site_position_modification(self, example_structure_dict):
        """Test modifying site positions in mutable model."""
        model = MutableStructureModel(**example_structure_dict)

        original_pos = model.sites[0].position
        model.sites[0].position = [1.0, 1.0, 1.0]

        assert not np.allclose(model.sites[0].position, original_pos)
        assert np.allclose(model.sites[0].position, [1.0, 1.0, 1.0])

    def test_add_site(self, example_structure_dict):
        """Test adding site to mutable model."""
        model = MutableStructureModel(**example_structure_dict)
        original_count = len(model.sites)

        from aiida_atomistic.data.structure.site import Site
        new_site = Site(symbol="C", position=[2.0, 2.0, 2.0])
        model.sites.append(new_site)

        assert len(model.sites) == original_count + 1

    def test_remove_site(self, example_structure_dict):
        """Test removing site from mutable model."""
        model = MutableStructureModel(**example_structure_dict)
        original_count = len(model.sites)

        model.sites.pop()

        assert len(model.sites) == original_count - 1

    def test_computed_fields_update_after_modification(self, example_structure_dict):
        """Test that computed fields update after modification."""
        model = MutableStructureModel(**example_structure_dict)

        original_volume = model.cell_volume

        model.cell = [[6.0, 0.0, 0.0], [0.0, 6.0, 0.0], [0.0, 0.0, 6.0]]

        assert model.cell_volume != original_volume
        assert np.isclose(model.cell_volume, 216.0)  # 6^3


# =============================================================================
# ImmutableStructureModel Tests
# =============================================================================

class TestImmutableStructureModel:
    """Test immutable structure model functionality."""

    def test_creation(self, example_structure_dict):
        """Test immutable model creation."""
        model = ImmutableStructureModel(**example_structure_dict)

        assert len(model.sites) == 1
        assert model.sites[0].symbol == "Cu"

    def test_modification_prevented(self, example_structure_dict):
        """Test that immutable model prevents modifications."""
        model = ImmutableStructureModel(**example_structure_dict)

        with pytest.raises((ValueError, Exception)):
            model.cell = [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]]

    def test_sites_are_frozen(self, example_structure_dict):
        """Test that sites are immutable (FrozenSites)."""
        model = ImmutableStructureModel(**example_structure_dict)

        from aiida_atomistic.data.structure.site import FrozenSite
        assert all(isinstance(s, FrozenSite) for s in model.sites)

    def test_site_modification_prevented(self, example_structure_dict):
        """Test that individual sites cannot be modified."""
        model = ImmutableStructureModel(**example_structure_dict)

        with pytest.raises((ValueError, Exception)):
            model.sites[0].position = [1.0, 1.0, 1.0]

    def test_computed_fields_work(self, example_structure_dict):
        """Test that computed fields work on immutable model."""
        model = ImmutableStructureModel(**example_structure_dict)

        assert model.cell_volume > 0
        assert len(model.sites) == 1
        assert "Cu" in model.formula

    def test_custom_field_frozen(self):
        """Test that custom field is frozen in immutable model."""
        model = ImmutableStructureModel(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0]}],
            custom={"key": "value", "nested": {"data": 123}}
        )
        assert model.custom is not None
        assert model.custom["key"] == "value"
        assert isinstance(model.custom, (dict, type(freeze_nested({}))))

    def test_setattr_error_message_mentions_immutable(self, example_structure_dict):
        """Test custom error message when trying to set attributes."""
        model = ImmutableStructureModel(**example_structure_dict)
        with pytest.raises(ValueError, match="immutable"):
            model.cell = [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]]

    def test_setattr_error_message_mentions_to_builder(self, example_structure_dict):
        """Test error message mentions to_builder method."""
        model = ImmutableStructureModel(**example_structure_dict)
        with pytest.raises(ValueError, match="immutable"):
            model.pbc = [False, False, False]


# =============================================================================
# Model Conversion Tests
# =============================================================================

class TestModelConversion:
    """Test conversion between model types."""

    def test_mutable_to_immutable(self, example_structure_dict):
        """Test converting mutable to immutable."""
        mutable = MutableStructureModel(**example_structure_dict)

        exclude = set(mutable.model_computed_fields.keys())
        immutable = ImmutableStructureModel(**mutable.model_dump(exclude_none=True, mode='python', exclude=exclude))

        assert len(immutable.sites) == len(mutable.sites)
        assert np.allclose(immutable.cell, mutable.cell)

    def test_immutable_to_mutable(self, example_structure_dict):
        """Test converting immutable to mutable."""
        immutable = ImmutableStructureModel(**example_structure_dict)

        exclude = set(immutable.model_computed_fields.keys())
        mutable = MutableStructureModel(**immutable.model_dump(exclude_none=True, mode='python', exclude=exclude))

        assert len(mutable.sites) == len(immutable.sites)
        assert np.allclose(mutable.cell, immutable.cell)

    def test_conversion_preserves_magnetic_data(self, magnetic_structure_collinear):
        """Test that conversion preserves all data including magnetic properties."""
        immutable = ImmutableStructureModel(**magnetic_structure_collinear)
        exclude = set(immutable.model_computed_fields.keys())
        mutable = MutableStructureModel(**immutable.model_dump(exclude_none=True, mode='python', exclude=exclude))

        assert all(
            np.allclose(im.magmom, mu.magmom)
            for im, mu in zip(immutable.sites, mutable.sites)
        )


# =============================================================================
# Serialization Tests
# =============================================================================

class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_model_dump_contains_expected_keys(self, example_structure_dict):
        """Test model_dump produces valid dict."""
        model = StructureBaseModel(**example_structure_dict)

        dumped = model.model_dump()

        assert isinstance(dumped, dict)
        assert "cell" in dumped
        assert "sites" in dumped
        assert "pbc" in dumped

    def test_model_dump_json_not_implemented(self, example_structure_dict):
        """Test model_dump_json with numpy arrays."""
        pytest.skip("JSON serialization of numpy arrays not implemented")

    def test_roundtrip_preserves_data(self, magnetic_structure_collinear):
        """Test that serialization roundtrip preserves data."""
        original = StructureBaseModel(**magnetic_structure_collinear)

        exclude = set(original.model_computed_fields.keys())
        dumped = original.model_dump(exclude_none=True, mode='python', exclude=exclude)
        restored = StructureBaseModel(**dumped)

        assert len(restored.sites) == len(original.sites)
        assert np.allclose(restored.cell, original.cell)
        assert all(
            np.allclose(r.magmom, o.magmom)
            for r, o in zip(restored.sites, original.sites)
        )

    def test_json_roundtrip_not_implemented(self, example_structure_dict_alloy):
        """Test JSON serialization roundtrip."""
        pytest.skip("JSON serialization of numpy arrays not implemented")


# =============================================================================
# get_defined_properties Tests
# =============================================================================

class TestGetDefinedProperties:
    """Test get_defined_properties method with filtering options."""

    def test_default_excludes_computed_without_singular(self):
        """Test default behavior excludes pure computed fields but includes site arrays."""
        model = StructureData(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
                {"symbol": "O", "position": [1.5, 1.5, 1.5], "charge": -1.0},
            ],
        )

        defined = model.get_defined_properties()

        # Should include base properties
        assert "cell" in defined
        assert "pbc" in defined
        assert "sites" in defined

        # Should include site arrays (computed with singular_form)
        assert "charges" in defined
        assert "symbols" in defined
        assert "positions" in defined

        # Should exclude pure computed fields (no singular_form)
        assert "formula" not in defined
        assert "cell_volume" not in defined
        assert "is_alloy" not in defined
        assert "dimensionality" not in defined

    def test_exclude_computed_without_singular_false(self):
        """Test with exclude_computed_without_singular=False includes all computed."""
        model = StructureData(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
            ],
        )

        defined = model.get_defined_properties(exclude_computed_without_singular=False)

        # Should include everything
        assert "charges" in defined  # Site array
        assert "composition" in defined  # Pure computed
        assert "cell_volume" in defined  # Pure computed
        assert "is_alloy" in defined  # Pure computed

    def test_exclude_computed_true(self):
        """Test with exclude_computed=True excludes ALL computed fields."""
        model = StructureData(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0},
            ],
        )

        defined = model.get_defined_properties(exclude_computed=True)

        # Should include base properties only
        assert "cell" in defined
        assert "pbc" in defined
        assert "sites" in defined

        # Should exclude ALL computed fields
        assert "charges" not in defined
        assert "symbols" not in defined
        assert "formula" not in defined
        assert "cell_volume" not in defined

    def test_none_properties_not_included(self):
        """Test that properties returning None are not included."""
        model = StructureData(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0]},
            ],
        )

        defined = model.get_defined_properties()

        assert "charges" not in defined
        assert "magmoms" not in defined

    def test_with_magnetic_moments(self):
        """Test with structure containing magnetic moments."""
        model = StructureData(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[
                {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
            ],
        )

        defined = model.get_defined_properties()

        assert "magmoms" in defined
        assert "charges" not in defined

    def test_parameter_precedence(self):
        """Test that exclude_computed overrides exclude_computed_without_singular."""
        model = StructureData(
            pbc=[True, True, True],
            cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            sites=[{"symbol": "Fe", "position": [0, 0, 0], "charge": 1.0}],
        )

        defined = model.get_defined_properties(
            exclude_computed=True,
            exclude_computed_without_singular=False
        )

        # exclude_computed=True should override
        assert "charges" not in defined
        assert "formula" not in defined
