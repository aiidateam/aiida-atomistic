from aiida.engine import calcfunction

from aiida_atomistic.data.structure.structure import StructureData
from aiida.orm import StructureData as LegacyStructureData

@calcfunction
def from_legacy_to_atomistic(legacy_structure: 'LegacyStructureData') -> 'StructureData':

    """Convert a legacy AiiDA StructureData to the new atomistic StructureData.

    Args:
        legacy_structure (LegacyStructureData): The legacy StructureData to convert.
    Returns:
        StructureData: The converted atomistic StructureData.

    Example::
        >>> from aiida import orm
        >>> from aiida_atomistic.data.structure.utils_orm import from_legacy_to_atomistic
        >>> legacy_structure = orm.StructureData(cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]], pbc=[True, True, True])
        >>> legacy_structure.append_atom(symbols='H', position=[0.0, 0.0, 0.0], mass=1.008, name='H1')
        >>> legacy_structure.append_atom(symbols='O', position=[0.0, 0.0, 1.0], mass=15.999, name='O1')

        >>> # Convert to atomistic StructureData, without storing provenance (for testing purposes; default is True)
        >>> atomistic_structure = from_legacy_to_atomistic(legacy_structure, metadata={'store_provenance': False})
        >>> print(atomistic_structure)

    """

    if not isinstance(legacy_structure, LegacyStructureData):
        raise TypeError(f'Expected a LegacyStructureData, got {type(legacy_structure)}')

    legacy_dict = {
        'pbc': legacy_structure.pbc,
        'cell': legacy_structure.cell,
        'sites': [
            {
                'symbol': legacy_structure.get_kind(site.kind_name).symbol,
                'mass': legacy_structure.get_kind(site.kind_name).mass,
                'position': site.position,
                'kind_name': site.kind_name,
                'weight': legacy_structure.get_kind(site.kind_name).weights,
            } for site in legacy_structure.sites
        ]
    }

    return StructureData(**legacy_dict)
