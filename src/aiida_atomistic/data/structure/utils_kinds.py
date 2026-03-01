import typing as t
import copy
import numpy as np

from aiida import orm

from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder
from aiida_atomistic.data.structure.utils import _get_computed_properties_from_model


def _get_global_properties(model_class):
    """Get list of global properties from model metadata."""
    global_props = []

    # Check regular fields
    for field_name, field_info in model_class.model_fields.items():
        extra = field_info.json_schema_extra or {}
        if extra.get("property_type", "") == "global":
            global_props.append(field_name)

    # Check computed fields
    for field_name, computed_field_info in model_class.model_computed_fields.items():
        extra = getattr(computed_field_info, "json_schema_extra", None) or {}
        if extra.get("property_type", "") == "global":
            global_props.append(field_name)

    return global_props


def _get_properties_with_singular_form(model_class):
    """Get list of global properties from model metadata."""
    _props = []

    # Check regular fields
    for field_name, field_info in model_class.model_fields.items():
        extra = field_info.json_schema_extra or {}
        if extra.get("singular_form", None) is not None:
            _props.append(field_name)

    # Check computed fields
    for field_name, computed_field_info in model_class.model_computed_fields.items():
        extra = getattr(computed_field_info, "json_schema_extra", None) or {}
        if extra.get("singular_form", None) is not None:
            _props.append(field_name)

    return _props


def compress_properties_by_kind(props, model_class=None):
    """
    Compress site-wise properties into kind-wise lists.
    Returns a dict with properties as lists, one entry per kind.

    Args:
        props: Dictionary of properties to compress
        model_class: The Pydantic model class (e.g., StructureProperties) to extract metadata from.
                    If not provided, will attempt to use StructureData.
    """
    import numpy as np

    if not props.get("kind_names", None):
        raise ValueError("The input properties must contain 'kind_names' information.")

    # Get model class if not provided
    if model_class is None:
        from aiida_atomistic.data.structure.models import StructureBaseModel

        model_class = StructureBaseModel

    kind_names_array = np.array(props["kind_names"])

    # Get global and computed properties dynamically from metadata
    global_props = _get_global_properties(model_class)
    computed_props = _get_computed_properties_from_model(model_class)

    site_props = set(props.keys()).difference(global_props + computed_props + ["sites"])

    full_set_of_props = site_props.union(global_props).union(["site_indices"])

    compressed = {
        prop: []
        if prop in site_props.union(["site_indices"])
        else props.get(prop, None)
        for prop in full_set_of_props
    }

    for kind_name in set(props["kind_names"]):
        site_indices = np.where(kind_names_array == kind_name)[0]
        for prop in site_props:
            if prop == "positions":
                compressed[prop].append([props[prop][i] for i in site_indices])
            elif prop in props and props[prop] is not None:
                compressed[prop].append(props[prop][site_indices[0]])
            else:
                compressed.pop(prop, None)
        compressed["site_indices"].append(site_indices.tolist())

    for prop in global_props:
        if compressed.get(prop, None) is None:
            compressed.pop(prop, None)

    return compressed


def rebuild_site_lists_from_kind_lists(compressed, model_class=None):
    """
    Expand kinds into a list of site dictionaries, sorted by site_index.

    Args:
        compressed: Dictionary of compressed kind-wise properties
        model_class: The Pydantic model class (e.g., StructureProperties) to extract metadata from.
                    If not provided, will attempt to use StructureData.
    """
    # Get model class if not provided
    if model_class is None:
        from aiida_atomistic.data.structure.models import StructureBaseModel

        model_class = StructureBaseModel

    # Get global and computed properties dynamically from metadata
    global_props = _get_global_properties(model_class)
    # computed_props = _get_computed_properties_from_model(model_class)
    props_with_singluar_form = _get_properties_with_singular_form(model_class)

    # Site props are properties that exist in compressed dict and need to be expanded
    # These are: properties with singular_form + 'site_indices' + 'positions'
    # Everything else (global props, pure computed props) should be kept as-is
    all_props_in_compressed = set(compressed.keys())

    # Properties that need expansion (site-wise)
    site_props = all_props_in_compressed.intersection(
        set(props_with_singluar_form + ["site_indices", "positions"])
    )

    # All properties to include in final dict
    full_set_of_props = all_props_in_compressed.union(global_props)

    # Initialize expanded dict
    expanded = {}
    for prop in full_set_of_props:
        if prop in site_props:
            # Site properties that need expansion start as empty lists
            expanded[prop] = []
        else:
            # Global properties and pure computed properties keep their values
            expanded[prop] = compressed.get(prop, None)

    # Also need to initialize any missing site-wise properties with singular forms as empty lists
    # for prop in props_with_singluar_form:
    #    if prop not in expanded:
    #        expanded[prop] = []

    # Now expand compressed properties back to per-site format
    # compressed['site_indices'] is a list of lists: [[0], [1]] means kind 0 has site 0, kind 1 has site 1
    # compressed['positions'] is a list of lists of positions: one list per kind
    # Other properties with singular_form are compressed: one value per kind, needs repetition

    for kind_idx, sites_in_kind in enumerate(compressed["site_indices"]):
        num_sites_in_kind = len(sites_in_kind)

        # Expand positions: compressed['positions'][kind_idx] is a list of position arrays
        if "positions" in compressed:
            for site_index in sites_in_kind:
                positions_for_kind = compressed["positions"][site_index]
                expanded["positions"].append(list(positions_for_kind))

        # Expand other properties with singular_form: repeat the single value for each site
        for prop in props_with_singluar_form:
            if prop == "positions":
                continue  # Already handled above
            if prop in compressed:
                value_for_kind = compressed[prop][kind_idx]
                # Repeat this value for each site in the kind
                expanded[prop].extend([value_for_kind] * num_sites_in_kind)

        # Track which original site indices we've added
        expanded["site_indices"].extend(sites_in_kind)

    # Remove None global properties
    for prop in global_props:
        if expanded.get(prop, None) is None:
            expanded.pop(prop, None)

    # Reorder everything by the original site index
    order = np.argsort(np.array(expanded["site_indices"]).flatten())

    # Reorder all properties with singular_form (including positions) plus site_indices
    for prop in props_with_singluar_form + ["positions", "site_indices"]:
        if (
            prop in expanded
            and isinstance(expanded[prop], list)
            and len(expanded[prop]) > 0
        ):
            expanded[prop] = [expanded[prop][i] for i in order]

    # Remove the site_indices tracking list
    expanded.pop("site_indices")

    return expanded


def classify_site_kinds(sites: list, threshold: dict = {}):
    """
    Classify sites into groups where each group (kind) has the same properties except position.

    Args:
        sites: List of site dictionaries
        exclude_props: Set of property names to exclude from grouping (default: {'position'})
        threshold: Numerical threshold for floating point comparisons (default: 1e-3)

    Returns:
        dict: {group_key: {'sites': [site_indices], 'properties': {prop: value}}}
    """
    import numpy as np
    from collections import defaultdict

    exclude_props = {"position"}

    def normalize_value(value, tol=threshold):
        """Normalize values for consistent comparison."""
        if isinstance(value, np.ndarray):
            # Round numpy arrays to threshold
            normalized = np.round(value / tol) * tol
            return tuple(normalized.tolist())
        elif isinstance(value, (float, np.floating)):
            # Round floats to threshold
            return round(value / tol) * tol
        elif isinstance(value, (int, np.integer)):
            return int(value)
        elif isinstance(value, list):
            # Convert lists to tuples (for alloy symbols, weights, etc.)
            return tuple(value)
        elif isinstance(value, tuple):
            # Already a tuple, return as-is
            return value
        elif value is None:
            return None
        else:
            return value

    groups = defaultdict(lambda: {"sites": [], "positions": [], "properties": {}})

    for i, site in enumerate(sites):
        # Create a hashable key from normalized properties
        key_props = {}
        for prop, value in site.items():
            if prop not in exclude_props:
                if isinstance(threshold, dict):
                    tol = threshold.get(prop, 1e-3)
                else:
                    tol = threshold
                normalized_value = normalize_value(value, tol)
                key_props[prop] = normalized_value

        # Create a hashable key containing both property names and their normalized values, so it is a unique identifier
        key = tuple(sorted(key_props.items()))

        # Add site index to this group (or this specific hashable key)
        groups[key]["sites"].append(i)
        groups[key]["positions"].append(site["position"])

        # Store the original properties (first occurrence) WITHOUT normalization
        if not groups[key]["properties"]:
            groups[key]["properties"] = {
                prop: value for prop, value in site.items() if prop not in exclude_props
            }

    return dict(groups)


def check_kinds_match(structure, kinds_list):
    check_kinds = []
    kind_names_indices = [kind["site_indices"] for kind in kinds_list]
    for kind in structure.kinds:
        site_indices = kind.site_indices
        check_kinds.append(site_indices in kind_names_indices)

    return all(check_kinds)


def sites_from_kinds(kinds):
    """
    Expand kinds into a list of site dictionaries, sorted by site_index.
    1. Create a list of site indices and positions from the kinds
    2. Create a list of site dictionaries by copying the kind properties
       and adding the position
    3. Return the list of site dictionaries
    4. Note: the returned list is sorted by site_index

    Format of kinds (basically what can be obtained by structure.generate_kinds()):
    [
        {'site_indices': [0, 2],
        'positions': [array([0., 0., 0.]), array([0., 1., 0.])],
        'symbol': 'H',
        'mass': 1.008,
        'charge': 0.0,
        'magmom': (0.0, 0.0, -1.0),
        'kind_name': 'H1'},
        {'site_indices': [1],
        'positions': [array([0., 0., 1.])],
        'symbol': 'O',
        'mass': 15.999,
        'charge': -2.0,
        'magmom': (0.0, 0.0, 1.0),
        'kind_name': 'O1'}
    ]
    """
    sites_list = []
    positions = []
    for i, kind in enumerate(kinds):
        sites_list += [i] * len(kind["site_indices"])
        positions += list(kind["positions"])
    num_sites = len(sites_list)
    for i in range(num_sites):
        sites_list[i] = copy.deepcopy(kinds[sites_list[i]])
        sites_list[i].pop("site_indices", None)
        sites_list[i].pop("positions", None)
        sites_list[i]["position"] = positions[i]

    return sites_list


def generate_kinds(
    structure: t.Union[StructureData, StructureBuilder], threshold: dict = {}
):
    """Generate kinds for a given structure by classifying sites based on their properties.

    Args:
        structure (Union[StructureData, StructureBuilder]): The structure to generate kinds for.
        threshold (Union[dict, float], optional): The threshold for classifying sites. Defaults to 1e-3.
                                                  If dict, keys are property names and values are thresholds.

    Returns:
        list[dict]: A list of kinds with their associated site indices and properties.
                    This can be directly used to initialize a StructureData/StructureBuilder instance.
    """

    if isinstance(threshold, orm.Dict):
        threshold = threshold.get_dict()

    sites = structure.to_dict()["sites"]
    for i, site in enumerate(sites):
        # Remove kind_name if already present, to avoid interference with classification
        sites[i].pop("kind_name", None)

    groups = classify_site_kinds(sites, threshold=threshold)
    kinds = []
    kind_names = []
    for i, (key, group) in enumerate(groups.items()):
        for l in range(i + 1):  # noqa: E741
            kind_name = f"{group['properties']['symbol']}{l + 1}"
            if kind_name not in kind_names:
                kind_names.append(kind_name)
                break
            else:
                continue

        site_indices = group["sites"]
        properties = group["properties"]
        positions = group["positions"]
        properties["kind_name"] = kind_name
        kind = {"site_indices": site_indices, "positions": positions, **properties}
        kinds.append(kind)

    return kinds


def to_kinds(structure: t.Union[StructureData, StructureBuilder], threshold: dict = {}):
    """Return a new StructureData/StructureBuilder instance with kinds generated from the sites.

    This function is called by the `to_kinds` method of StructureData and StructureBuilder GetterMixin class.
    It can be dressed via the calcfunction decorator to store provenance if needed (i.e. if the structure is a StructureData).

    Args:
        structure (Union[StructureData, StructureBuilder]): The structure to generate kinds for.
        threshold (Union[dict, float], optional): The threshold for classifying sites. Defaults to 1e-3.
                                                  If dict, keys are property names and values are thresholds.

    Returns:
        Union[StructureData, StructureBuilder]: A new instance of the same type as the input structure,
                                                but with kinds generated from the sites.
    """
    dict_repr = structure.to_dict()

    dict_repr["kinds"] = generate_kinds(structure, threshold=threshold)
    dict_repr.pop("sites", None)

    if isinstance(structure, StructureData):
        return StructureData(**dict_repr)
    elif isinstance(structure, StructureBuilder):
        return StructureBuilder(**dict_repr)
    else:
        raise TypeError(
            f"Expected a StructureData or StructureBuilder, got {type(structure)}"
        )
