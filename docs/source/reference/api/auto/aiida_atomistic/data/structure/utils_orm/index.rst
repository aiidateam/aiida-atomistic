:py:mod:`aiida_atomistic.data.structure.utils_orm`
==================================================

.. py:module:: aiida_atomistic.data.structure.utils_orm


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.utils_orm.from_legacy_to_atomistic



.. py:function:: from_legacy_to_atomistic(legacy_structure: aiida.orm.StructureData) -> aiida_atomistic.data.structure.structure.StructureData

   Convert a legacy AiiDA StructureData to the new atomistic StructureData.

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
