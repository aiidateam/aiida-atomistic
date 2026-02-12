:py:mod:`aiida_atomistic.data.structure.structure`
==================================================

.. py:module:: aiida_atomistic.data.structure.structure


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.structure.StructureData
   aiida_atomistic.data.structure.structure.StructureBuilder




.. py:class:: StructureData(sites: list[dict] = None, kinds: list[dict] = None, **kwargs)


   Bases: :py:obj:`aiida.orm.nodes.data.Data`, :py:obj:`aiida_atomistic.data.structure.getter_mixin.GetterMixin`

   A StructureData class that stores properties in the repository instead of attributes.

   This class stores selected properties in a single compressed .npz file in the repository.
   Only properties useful for querying are stored in database attributes.

   This approach is more efficient for large structures as it avoids storing
   large arrays in the database.

   .. py:property:: properties

      Reconstruct the properties model from stored data.

      For stored nodes, this reads from attributes and the npz file in repository.
      For unstored nodes, returns the in-memory properties.

      The reconstructed model is cached to avoid re-running validators on every access.


   .. py:attribute:: _mutable
      :value: False



   .. py:attribute:: _model



   .. py:attribute:: _properties_filename
      :value: 'properties.npz'



   .. py:attribute:: _store_shape_metadata
      :value: False



   .. py:attribute:: _storage_metadata_key
      :value: 'store_in'



   .. py:attribute:: _storage_repository_values



   .. py:attribute:: _storage_attribute_values



   .. py:method:: _is_numeric_array(value) -> bool
      :staticmethod:

      Return True if the value is a numeric numpy array (or convertible).


   .. py:method:: get_queryable_properties(include_internal: bool = False) -> dict
      :classmethod:

      Get all properties that can be queried via QueryBuilder.

      For repository-based storage, ONLY properties stored in database attributes
      are queryable. Properties stored in .npz files CANNOT be queried directly.

      :param include_internal: If True, include internal properties like 'sites'.
                               Default is False.
      :return: Dictionary with property classifications:
               - 'queryable': Properties stored in database (can be queried)
               - 'not_queryable': Properties stored in .npz or not stored (cannot be queried)

      Example:
          >>> props = StructureData.get_queryable_properties()
          >>> print(props['queryable'])
          ['cell', 'cell_volume', 'custom', 'dimensionality', 'formula',
           'has_vacancies', 'is_alloy', 'kind_names', 'max_charge',
           'min_charge', 'n_sites', 'pbc', 'symbols', 'tot_charge', ...]
          >>> print(props['not_queryable'])
          ['charges', 'kinds', 'magmoms', 'magnetizations', 'masses',
           'positions', 'weights']


   .. py:method:: print_queryable_properties()
      :classmethod:

      Print a formatted overview of which properties can be queried.

      This is useful for understanding what properties are available for
      filtering in QueryBuilder when using repository-based storage.

      IMPORTANT: Only properties stored in database attributes can be queried.
      Properties stored in .npz files are not queryable via QueryBuilder.

      Example:
          >>> StructureData.print_queryable_properties()

          ═══════════════════════════════════════════════════════════════
          Queryable Properties for StructureData
          ═══════════════════════════════════════════════════════════════

          ✓ QUERYABLE (stored in database attributes):
            • cell
            • cell_volume
            • custom
            • dimensionality
            • formula
            • has_vacancies
            • is_alloy
            • kind_names
            • max_charge
            • max_magmom
            • max_magnetization
            • min_charge
            • min_magmom
            • min_magnetization
            • n_sites
            • pbc
            • symbols
            • tot_charge
            • tot_magnetization

          ✗ NOT QUERYABLE (stored in .npz repository):
            • charges
            • magmoms
            • magnetizations
            • masses
            • positions
            • weights

          ⚠ NOT QUERYABLE (computed on-the-fly, not stored):
            • kinds

          Note: Use QueryBuilder filters only on queryable properties.
                Example: qb.append(StructureData,
                                  filters={'attributes.formula': 'Si2',
                                          'attributes.max_charge': {'>': 0.5}})


   .. py:method:: detect_storage_backend(prop_name: str) -> str
      :classmethod:

      Detect the storage backend for a property based on its metadata.

      :param prop_name: Name of the property
      :return: Storage backend ('db', 'npz', 'repo', etc.)


   .. py:method:: _store_properties()

      Store properties in the AiiDA db and/or in a single npz file in the repository.


   .. py:method:: _load_properties_from_npz() -> dict

      Load all properties from the npz file in the repository.

      :return: Dictionary of property name -> numpy array


   .. py:method:: from_builder(builder: StructureBuilder)
      :classmethod:

      Create a StructureData from a StructureBuilder.


   .. py:method:: to_builder() -> StructureBuilder

      Convert to a mutable StructureBuilder.


   .. py:method:: __repr__() -> str

      Return a concise string representation of the structure.


   .. py:method:: __str__() -> str

      Return a string representation of the structure for print().


   .. py:method:: _validate() -> bool

      Validate the node.

      Check that npz metadata in attributes matches properties in npz file.



.. py:class:: StructureBuilder(sites: list[dict] = None, kinds: list[dict] = None, **kwargs)


   Bases: :py:obj:`aiida_atomistic.data.structure.getter_mixin.GetterMixin`, :py:obj:`aiida_atomistic.data.structure.setter_mixin.SetterMixin`

   .. py:property:: properties


   .. py:attribute:: _mutable
      :value: True



   .. py:attribute:: _model



   .. py:method:: from_aiida(aiida: StructureData)
      :classmethod:


   .. py:method:: to_aiida() -> StructureData


   .. py:method:: __repr__() -> str

      Return a concise string representation of the structure.


   .. py:method:: __str__() -> str

      Return a string representation of the structure for print().
