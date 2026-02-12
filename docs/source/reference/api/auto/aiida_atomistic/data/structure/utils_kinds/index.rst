:py:mod:`aiida_atomistic.data.structure.utils_kinds`
====================================================

.. py:module:: aiida_atomistic.data.structure.utils_kinds


Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.utils_kinds._get_global_properties
   aiida_atomistic.data.structure.utils_kinds._get_properties_with_singular_form
   aiida_atomistic.data.structure.utils_kinds._get_computed_properties
   aiida_atomistic.data.structure.utils_kinds.compress_properties_by_kind
   aiida_atomistic.data.structure.utils_kinds.rebuild_site_lists_from_kind_lists
   aiida_atomistic.data.structure.utils_kinds.classify_site_kinds
   aiida_atomistic.data.structure.utils_kinds.check_kinds_match
   aiida_atomistic.data.structure.utils_kinds.sites_from_kinds
   aiida_atomistic.data.structure.utils_kinds.generate_kinds
   aiida_atomistic.data.structure.utils_kinds.to_kinds



.. py:function:: _get_global_properties(model_class)

   Get list of global properties from model metadata.


.. py:function:: _get_properties_with_singular_form(model_class)

   Get list of global properties from model metadata.


.. py:function:: _get_computed_properties(model_class)

   Get list of computed properties from model metadata.


.. py:function:: compress_properties_by_kind(props, model_class=None)

   Compress site-wise properties into kind-wise lists.
   Returns a dict with properties as lists, one entry per kind.

   Args:
       props: Dictionary of properties to compress
       model_class: The Pydantic model class (e.g., StructureProperties) to extract metadata from.
                   If not provided, will attempt to use StructureData.


.. py:function:: rebuild_site_lists_from_kind_lists(compressed, model_class=None)

   Expand kinds into a list of site dictionaries, sorted by site_index.

   Args:
       compressed: Dictionary of compressed kind-wise properties
       model_class: The Pydantic model class (e.g., StructureProperties) to extract metadata from.
                   If not provided, will attempt to use StructureData.


.. py:function:: classify_site_kinds(sites: list, threshold: dict = {})

   Classify sites into groups where each group (kind) has the same properties except position.

   Args:
       sites: List of site dictionaries
       exclude_props: Set of property names to exclude from grouping (default: {'position'})
       threshold: Numerical threshold for floating point comparisons (default: 1e-3)

   Returns:
       dict: {group_key: {'sites': [site_indices], 'properties': {prop: value}}}


.. py:function:: check_kinds_match(structure, kinds_list)


.. py:function:: sites_from_kinds(kinds)

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


.. py:function:: generate_kinds(structure: Union[aiida_atomistic.data.structure.structure.StructureData, aiida_atomistic.data.structure.structure.StructureBuilder], threshold: dict = {})

   Generate kinds for a given structure by classifying sites based on their properties.

   Args:
       structure (Union[StructureData, StructureBuilder]): The structure to generate kinds for.
       threshold (Union[dict, float], optional): The threshold for classifying sites. Defaults to 1e-3.
                                                 If dict, keys are property names and values are thresholds.

   Returns:
       list[dict]: A list of kinds with their associated site indices and properties.
                   This can be directly used to initialize a StructureData/StructureBuilder instance.


.. py:function:: to_kinds(structure: Union[aiida_atomistic.data.structure.structure.StructureData, aiida_atomistic.data.structure.structure.StructureBuilder], threshold: dict = {})

   Return a new StructureData/StructureBuilder instance with kinds generated from the sites.

   This function is called by the `to_kinds` method of StructureData and StructureBuilder GetterMixin class.
   It can be dressed via the calcfunction decorator to store provenance if needed (i.e. if the structure is a StructureData).

   Args:
       structure (Union[StructureData, StructureBuilder]): The structure to generate kinds for.
       threshold (Union[dict, float], optional): The threshold for classifying sites. Defaults to 1e-3.
                                                 If dict, keys are property names and values are thresholds.

   Returns:
       Union[StructureData, StructureBuilder]: A new instance of the same type as the input structure,
                                               but with kinds generated from the sites.
