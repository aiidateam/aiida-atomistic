import typing as t

from aiida import orm
from aiida.engine import calcfunction

from aiida_atomistic.data.structure.structure import StructureData, StructureBuilder
from aiida_atomistic.data.structure.utils import classify_site_kinds

def generate_kinds(structure: t.Union[StructureData, StructureBuilder], tolerance:t.Union[dict, float]=1e-3):
    """Generate kinds for a given structure by classifying sites based on their properties.

    Args:
        structure (Union[StructureData, StructureBuilder]): The structure to generate kinds for.
        tolerance (Union[dict, float], optional): The tolerance for classifying sites. Defaults to 1e-3.
                                                  If dict, keys are property names and values are tolerances.

    Returns:
        list[dict]: A list of kinds with their associated site indices and properties.
                    This can be directly used to initialize a StructureData/StructureBuilder instance.
    """

    if isinstance(tolerance, orm.Float):
        tolerance = tolerance.value
    elif isinstance(tolerance, orm.Dict):
        tolerance = tolerance.get_dict()

    sites = structure.to_dict()['sites']
    groups = classify_site_kinds(sites, tolerance=tolerance)
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

def to_kinds(structure: t.Union[StructureData, StructureBuilder], tolerance:t.Union[dict, float]=1e-3):
    """Return a new StructureData/StructureBuilder instance with kinds generated from the sites.

    This function is called by the `to_kinds` method of StructureData and StructureBuilder GetterMixin class.
    It can be dressed via the calcfunction decorator to store provenance if needed (i.e. if the structure is a StructureData).

    Args:
        structure (Union[StructureData, StructureBuilder]): The structure to generate kinds for.
        tolerance (Union[dict, float], optional): The tolerance for classifying sites. Defaults to 1e-3.
                                                  If dict, keys are property names and values are tolerances.

    Returns:
        Union[StructureData, StructureBuilder]: A new instance of the same type as the input structure,
                                                but with kinds generated from the sites.
    """
    dict_repr = structure.to_dict()
    dict_repr['kinds'] = generate_kinds(structure, tolerance=tolerance)
    dict_repr.pop('sites', None)

    if isinstance(structure, StructureData):
        return StructureData(**dict_repr)
    elif isinstance(structure, StructureBuilder):
        return StructureBuilder(**dict_repr)
    else:
        raise TypeError(f"Expected a StructureData or StructureBuilder, got {type(structure)}")
