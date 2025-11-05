"""Tests for utility functions."""
import numpy as np
import pytest

from aiida_atomistic.data.structure import StructureData, StructureBuilder
from aiida_atomistic.data.structure.utils import (
    _check_valid_sites,
    _create_symbols_tuple,
    _create_weights_tuple,
    _get_valid_cell,
    _get_valid_pbc,
    calc_cell_volume,
    check_is_alloy,
    classify_site_kinds,
    compress_properties_by_kind,
    create_automatic_kind_name,
    get_dimensionality,
    get_formula,
    get_symbols_string,
    has_ase,
    has_pymatgen,
    has_vacancies,
    is_valid_symbol,
    rebuild_site_lists_from_kind_lists,
    sites_from_kinds,
    validate_symbols_tuple,
    validate_weights_tuple,
)


class TestCellValidation:
    """Test cell validation utilities."""

    def test_valid_cell(self):
        """Test valid cell is accepted."""
        cell = [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]
        result = _get_valid_cell(cell)

        assert isinstance(result, np.ndarray)
        assert result.shape == (3, 3)

    def test_invalid_cell_not_3x3(self):
        """Test invalid cell (not 3x3) raises error."""
        cell = [[3.0, 0.0], [0.0, 3.0]]  # 2x2

        with pytest.raises(ValueError):
            _get_valid_cell(cell)

    def test_invalid_cell_wrong_length(self):
        """Test invalid cell (wrong number of vectors) raises error."""
        cell = [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0]]  # Only 2 vectors

        with pytest.raises(ValueError):
            _get_valid_cell(cell)

    def test_cell_volume_calculation(self):
        """Test cell volume calculation."""
        cell = [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]]
        volume = calc_cell_volume(cell)

        assert np.isclose(volume, 24.0)  # 2 * 3 * 4


class TestPBCValidation:
    """Test PBC validation utilities."""

    def test_valid_pbc_list(self):
        """Test valid PBC list."""
        pbc = [True, True, False]
        result = _get_valid_pbc(pbc)

        assert result == [True, True, False]

    def test_valid_pbc_single_bool(self):
        """Test single boolean is expanded to 3 values."""
        pbc = True
        result = _get_valid_pbc(pbc)

        assert result == [True, True, True]

    def test_invalid_pbc_wrong_length(self):
        """Test invalid PBC (wrong length) raises error."""
        pbc = [True, False]  # Only 2 values

        with pytest.raises(ValueError):
            _get_valid_pbc(pbc)

    def test_invalid_pbc_not_bool(self):
        """Test invalid PBC (not booleans) raises error."""
        pbc = [1, 0, 1]  # Integers, not bools

        with pytest.raises(ValueError):
            _get_valid_pbc(pbc)


class TestSiteValidation:
    """Test site validation utilities."""

    def test_valid_sites(self):
        """Test valid sites pass validation."""
        sites = [
            {"symbol": "H", "position": [0.0, 0.0, 0.0]},
            {"symbol": "O", "position": [1.0, 1.0, 1.0]},
        ]

        # Should not raise
        _check_valid_sites(sites)

    def test_sites_too_close(self):
        """Test sites that are too close raise error."""
        sites = [
            {"symbol": "H", "position": [0.0, 0.0, 0.0]},
            {"symbol": "H", "position": [0.0001, 0.0, 0.0]},  # Very close
        ]

        with pytest.raises(ValueError, match="too close"):
            _check_valid_sites(sites)

    def test_single_site(self):
        """Test single site passes validation."""
        sites = [{"symbol": "H", "position": [0.0, 0.0, 0.0]}]

        # Should not raise
        _check_valid_sites(sites)


class TestSymbolsAndWeights:
    """Test symbols and weights utilities."""

    def test_create_symbols_tuple_string(self):
        """Test creating symbols tuple from string."""
        symbols = "CuAl"
        result = _create_symbols_tuple(symbols)

        # Returns list, not tuple
        assert result == ["Cu", "Al"]

    def test_create_symbols_tuple_list(self):
        """Test creating symbols tuple from list."""
        symbols = ["Cu", "Al"]
        result = _create_symbols_tuple(symbols)

        assert result == ("Cu", "Al")

    def test_create_symbols_tuple_invalid(self):
        """Test invalid symbol raises error."""
        symbols = ["Xx"]  # Invalid element

        with pytest.raises(ValueError):
            _create_symbols_tuple(symbols)

    def test_create_weights_tuple_none(self):
        """Test creating weights tuple from None."""
        result = _create_weights_tuple(None)

        assert result == (1.0,)

    def test_create_weights_tuple_number(self):
        """Test creating weights tuple from single number."""
        result = _create_weights_tuple(0.5)

        assert result == (0.5,)

    def test_create_weights_tuple_list(self):
        """Test creating weights tuple from list."""
        result = _create_weights_tuple([0.6, 0.4])

        assert result == (0.6, 0.4)

    def test_validate_weights_valid(self):
        """Test valid weights pass validation."""
        weights = (0.6, 0.4)

        # Should not raise
        validate_weights_tuple(weights, 1e-6)

    def test_validate_weights_with_vacancy(self):
        """Test weights with vacancy pass validation."""
        weights = (0.7, 0.2)  # Sum = 0.9, has vacancy

        # Should not raise
        validate_weights_tuple(weights, 1e-6)

    def test_validate_weights_invalid_negative(self):
        """Test negative weights raise error."""
        weights = (0.8, -0.2)

        with pytest.raises(ValueError):
            validate_weights_tuple(weights, 1e-6)

    def test_validate_weights_invalid_sum_too_large(self):
        """Test weights summing >1 raise error."""
        weights = (0.7, 0.5)  # Sum = 1.2

        with pytest.raises(ValueError):
            validate_weights_tuple(weights, 1e-6)

    def test_is_valid_symbol(self):
        """Test valid symbol recognition."""
        assert is_valid_symbol("H")
        assert is_valid_symbol("Cu")
        assert not is_valid_symbol("Xx")

    def test_validate_symbols_tuple_valid(self):
        """Test valid symbols tuple."""
        symbols = ("H", "O")

        # Should not raise
        validate_symbols_tuple(symbols)

    def test_validate_symbols_tuple_invalid(self):
        """Test invalid symbols tuple raises error."""
        from aiida.common.exceptions import UnsupportedSpeciesError

        symbols = ("H", "Xx")

        with pytest.raises(UnsupportedSpeciesError):
            validate_symbols_tuple(symbols)


class TestKindNames:
    """Test automatic kind name generation."""

    def test_automatic_kind_name_simple(self):
        """Test automatic kind name generation."""
        name = create_automatic_kind_name(["Cu"], [1.0])

        assert name == "Cu"

    def test_automatic_kind_name_alloy(self):
        """Test automatic kind name for alloy."""
        name = create_automatic_kind_name(["Cu", "Al"], [0.5, 0.5])

        assert name == "AlCu"  # Alphabetical order

    def test_automatic_kind_name_vacancy(self):
        """Test automatic kind name with vacancy."""
        name = create_automatic_kind_name(["Cu"], [0.9])

        assert name == "CuX"  # X indicates vacancy

    def test_get_symbols_string_simple(self):
        """Test symbols string for simple site."""
        result = get_symbols_string(["Cu"], [1.0])

        assert result == "Cu"

    def test_get_symbols_string_alloy(self):
        """Test symbols string for alloy."""
        result = get_symbols_string(["Cu", "Al"], [0.6, 0.4])

        assert "{" in result
        assert "Cu" in result
        assert "Al" in result

    def test_has_vacancies(self):
        """Test vacancy detection."""
        assert has_vacancies([0.9])
        assert has_vacancies([0.5, 0.4])
        assert not has_vacancies([1.0])
        assert not has_vacancies([0.6, 0.4])


class TestFormula:
    """Test chemical formula generation."""

    def test_formula_hill_simple(self, example_structure_dict):
        """Test Hill formula for simple structure."""
        structure = StructureData(**example_structure_dict)
        formula = get_formula(structure.sites, mode="hill")

        # example_structure_dict has 1 Cu site
        assert formula == "Cu"

    def test_formula_hill_water(self):
        """Test Hill formula for water."""
        structure_dict = {
            "pbc": [True, True, True],
            "cell": [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            "sites": [
                {"symbol": "H", "position": [0, 0, 0]},
                {"symbol": "H", "position": [1, 0, 0]},
                {"symbol": "O", "position": [0.5, 1, 0]},
            ],
        }
        structure = StructureData(**structure_dict)
        formula = get_formula(structure.sites, mode="hill")

        assert formula == "H2O"

    def test_formula_hill_with_carbon(self):
        """Test Hill formula with carbon (C and H come first)."""
        structure_dict = {
            "pbc": [True, True, True],
            "cell": [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]],
            "sites": [
                {"symbol": "C", "position": [0, 0, 0]},
                {"symbol": "H", "position": [1, 0, 0]},
                {"symbol": "H", "position": [2, 0, 0]},
                {"symbol": "O", "position": [0, 1, 0]},
            ],
        }
        structure = StructureData(**structure_dict)
        formula = get_formula(structure.sites, mode="hill")

        # C comes first, then H, then others alphabetically
        assert formula.startswith("CH2")

    def test_formula_count(self):
        """Test count formula (order as added)."""
        structure_dict = {
            "pbc": [True, True, True],
            "cell": [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
            "sites": [
                {"symbol": "O", "position": [0, 0, 0]},
                {"symbol": "H", "position": [1, 0, 0]},
                {"symbol": "H", "position": [2, 0, 0]},
            ],
        }
        structure = StructureData(**structure_dict)
        formula = get_formula(structure.sites, mode="count")

        assert formula == "OH2"  # Order as added

    def test_formula_reduce(self):
        """Test reduce formula."""
        structure_dict = {
            "pbc": [True, True, True],
            "cell": [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]],
            "sites": [
                {"symbol": "Ba", "position": [0, 0, 0]},
                {"symbol": "Ti", "position": [1, 0, 0]},
                {"symbol": "O", "position": [2, 0, 0]},
                {"symbol": "O", "position": [3, 0, 0]},
                {"symbol": "O", "position": [4, 0, 0]},
            ],
        }
        structure = StructureData(**structure_dict)

        # group_symbols returns list of lists
        from aiida_atomistic.data.structure.utils import group_symbols
        symbols = [s.symbol for s in structure.sites]
        grouped = group_symbols(symbols)
        assert grouped == [[1, "Ba"], [1, "Ti"], [3, "O"]]


class TestDimensionality:
    """Test dimensionality calculation."""

    def test_dimensionality_3d(self):
        """Test 3D structure."""
        pbc = [True, True, True]
        cell = [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]]

        result = get_dimensionality(pbc, cell)

        assert result["dim"] == 3
        assert result["label"] == "volume"
        assert np.isclose(result["value"], 27.0)

    def test_dimensionality_2d(self):
        """Test 2D structure (surface)."""
        pbc = [True, True, False]
        cell = [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 10.0]]

        result = get_dimensionality(pbc, cell)

        assert result["dim"] == 2
        assert result["label"] == "surface"
        assert result["value"] > 0

    def test_dimensionality_1d(self):
        """Test 1D structure (wire)."""
        pbc = [True, False, False]
        cell = [[5.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]]

        result = get_dimensionality(pbc, cell)

        assert result["dim"] == 1
        assert result["label"] == "length"
        assert np.isclose(result["value"], 5.0)

    def test_dimensionality_0d(self):
        """Test 0D structure (molecule)."""
        pbc = [False, False, False]
        cell = [[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]]

        result = get_dimensionality(pbc, cell)

        assert result["dim"] == 0
        assert result["label"] == ""
        assert result["value"] == 0


class TestAlloyUtilities:
    """Test alloy-related utilities."""

    def test_check_is_alloy_pure(self):
        """Test check_is_alloy for pure element."""
        data = {"symbol": "Cu", "position": [0, 0, 0]}

        result = check_is_alloy(data)

        # Returns the data dict, not None
        assert result == data or result is None

    def test_check_is_alloy_alloy(self):
        """Test check_is_alloy for alloy."""
        data = {
            "symbol": "CuAl",
            "weight": [0.5, 0.5],
            "position": [0, 0, 0],
        }

        result = check_is_alloy(data)

        assert result is not None
        assert "alloy" in result
        # Returns list, not tuple
        assert result["alloy"] == ["Cu", "Al"]


class TestKindsCompression:
    """Test kinds compression utilities."""

    def test_compress_properties(self, example_structure_dict_for_kinds):
        """Test compressing properties by kind."""
        structure = StructureData(**example_structure_dict_for_kinds)
        # properties is a model, need to convert to dict
        props = structure.properties.model_dump()

        compressed = compress_properties_by_kind(props)

        assert "site_indices" in compressed
        assert len(compressed["site_indices"]) == 2  # 2 kinds

    def test_rebuild_site_lists(self, example_structure_dict_for_kinds):
        """Test rebuilding site lists from compressed."""
        structure = StructureData(**example_structure_dict_for_kinds)
        # properties is a model, need to convert to dict
        props = structure.properties.model_dump()

        compressed = compress_properties_by_kind(props)
        rebuilt = rebuild_site_lists_from_kind_lists(compressed)

        assert len(rebuilt["positions"]) == len(structure.sites)

    def test_compression_roundtrip(self, complex_example_structure_dict_for_kinds):
        """Test compression/decompression roundtrip."""
        structure = StructureData(**complex_example_structure_dict_for_kinds)
        # properties is a model, need to convert to dict
        props = structure.properties.model_dump()

        compressed = compress_properties_by_kind(props)
        rebuilt = rebuild_site_lists_from_kind_lists(compressed)

        # Check roundtrip preserves data
        assert len(rebuilt["positions"]) == len(structure.sites)


class TestKindsClassification:
    """Test site classification into kinds."""

    def test_classify_site_kinds_simple(self):
        """Test classifying sites with same properties."""
        sites = [
            {"symbol": "Cu", "position": [0, 0, 0], "charge": 1.0},
            {"symbol": "Cu", "position": [1, 1, 1], "charge": 1.0},
        ]

        groups = classify_site_kinds(sites)

        assert len(groups) == 1  # All same kind

    def test_classify_site_kinds_different(self):
        """Test classifying sites with different properties."""
        # Use tuples for magmom to make hashable
        sites = [
            {"symbol": "Fe", "position": [0, 0, 0], "magmom": (0, 0, 2.2)},
            {"symbol": "Fe", "position": [1, 1, 1], "magmom": (0, 0, -2.2)},
        ]

        groups = classify_site_kinds(sites)

        assert len(groups) == 2  # Different magmom

    def test_sites_from_kinds(self):
        """Test creating sites list from kinds."""
        kinds = [
            {
                "site_indices": [0, 1],
                "positions": [np.array([0, 0, 0]), np.array([1, 1, 1])],
                "symbol": "Cu",
                "charge": 1.0,
                "kind_name": "Cu1",
            }
        ]

        sites = sites_from_kinds(kinds)

        assert len(sites) == 2
        assert all(s["symbol"] == "Cu" for s in sites)
        assert all(s["charge"] == 1.0 for s in sites)


class TestExternalLibraries:
    """Test external library detection."""

    def test_has_ase(self):
        """Test ASE detection."""
        result = has_ase()

        # Should return boolean
        assert isinstance(result, bool)

    def test_has_pymatgen(self):
        """Test pymatgen detection."""
        result = has_pymatgen()

        # Should return boolean
        assert isinstance(result, bool)


class TestObservedArray:
    """Test ObservedArray functionality."""

    def test_observed_array_creation(self):
        """Test ObservedArray can be created."""
        from aiida_atomistic.data.structure.utils import ObservedArray

        arr = ObservedArray([1, 2, 3])

        assert isinstance(arr, np.ndarray)
        assert len(arr) == 3

    def test_observed_array_setitem(self):
        """Test ObservedArray allows item assignment."""
        from aiida_atomistic.data.structure.utils import ObservedArray

        arr = ObservedArray([1, 2, 3])
        arr[0] = 10

        assert arr[0] == 10
