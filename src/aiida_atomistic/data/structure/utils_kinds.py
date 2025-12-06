import typing as t
import copy
import numpy as np

from aiida import orm

from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder

from .constants import _GLOBAL_PROPERTIES, _COMPUTED_PROPERTIES

def compress_properties_by_kind(props):
    """
    Compress site-wise properties into kind-wise lists.
    Returns a dict with properties as lists, one entry per kind.
    """
    import numpy as np

    if not props.get("kind_names", None):
        raise ValueError("The input properties must contain 'kind_names' information.")

    kind_names_array = np.array(props["kind_names"])

    site_props = set(props.keys()).difference(_GLOBAL_PROPERTIES + _COMPUTED_PROPERTIES + ["sites"])


    compressed = {prop: [] if prop in site_props.union(["site_indices"]) else props.get(prop, None) for prop in site_props.union(["site_indices"]).union(_GLOBAL_PROPERTIES)}

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

    for prop in _GLOBAL_PROPERTIES:
        if compressed.get(prop, None) is None:
            compressed.pop(prop, None)

    return compressed


def rebuild_site_lists_from_kind_lists(compressed):
    """
    Expand kinds into a list of site dictionaries, sorted by site_index.
    """
    site_props = set(compressed.keys()).difference(_GLOBAL_PROPERTIES + _COMPUTED_PROPERTIES + ["sites","site_indices"])
    expanded = {prop: [] if prop in site_props.union(["site_indices"]) else compressed.get(prop, None) for prop in site_props.union(["site_indices"]).union(_GLOBAL_PROPERTIES)}

    for i, site_indices in enumerate(compressed["site_indices"]):
        for prop in site_props:
            if prop == "positions":
                expanded[prop].extend(compressed[prop][i])
            elif prop == "site_indices":
                continue
            elif prop in compressed:
                expanded[prop].extend([compressed[prop][i]] * len(site_indices))
            else:
                expanded.pop(prop)

        expanded["site_indices"] += site_indices

    # Reorder by site_index
    order = np.argsort(expanded["site_indices"])
    for prop in site_props.union(["site_indices"]):
        if prop in expanded:
            expanded[prop] = [expanded[prop][i] for i in order]

    for prop in _GLOBAL_PROPERTIES:
        if expanded.get(prop, None) is None:
            expanded.pop(prop, None)

    expanded.pop("site_indices")

    return expanded

def classify_site_kinds(sites:list, threshold:dict={}):
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

    exclude_props = {'position'}

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

    groups = defaultdict(lambda: {'sites': [], 'positions': [], 'properties': {}})

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
        groups[key]['sites'].append(i)
        groups[key]['positions'].append(site['position'])

        # Store the original properties (first occurrence) WITHOUT normalization
        if not groups[key]['properties']:
            groups[key]['properties'] = {
                prop: value for prop, value in site.items()
                if prop not in exclude_props
            }

    return dict(groups)

def check_kinds_match(structure, kinds_list):
    check_kinds = []
    kind_names_indices = [kind['site_indices'] for kind in kinds_list]
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
    for i,kind in enumerate(kinds):
        sites_list += [i]*len(kind['site_indices'])
        positions += list(kind['positions'])
    num_sites = len(sites_list)
    for i in range(num_sites):
        sites_list[i] = copy.deepcopy(kinds[sites_list[i]])
        sites_list[i].pop('site_indices', None)
        sites_list[i].pop('positions', None)
        sites_list[i]['position'] = positions[i]

    return sites_list


def generate_kinds(structure: t.Union[StructureData, StructureBuilder], threshold: dict = {}):
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

    sites = structure.to_dict()['sites']
    groups = classify_site_kinds(sites, threshold=threshold)
    kinds = []
    kind_names = []
    for i, (key, group) in enumerate(groups.items()):
        for l in range(i+1):
            kind_name = f"{group['properties']['symbol']}{l+1}"
            if kind_name not in kind_names:
                kind_names.append(kind_name)
                break
            else:
                continue

        site_indices = group['sites']
        properties = group['properties']
        positions = group['positions']
        properties['kind_name'] = kind_name
        kind = {
            'site_indices': site_indices,
            'positions': positions,
            **properties
        }
        kinds.append(kind)
    return kinds

def to_kinds(structure: t.Union[StructureData, StructureBuilder], threshold:dict = {}):
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
    dict_repr['kinds'] = generate_kinds(structure, threshold=threshold)
    dict_repr.pop('sites', None)

    if isinstance(structure, StructureData):
        return StructureData(**dict_repr)
    elif isinstance(structure, StructureBuilder):
        return StructureBuilder(**dict_repr)
    else:
        raise TypeError(f"Expected a StructureData or StructureBuilder, got {type(structure)}")
