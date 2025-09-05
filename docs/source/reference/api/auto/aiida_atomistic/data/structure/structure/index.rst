:py:mod:`aiida_atomistic.data.structure.structure`
==================================================

.. py:module:: aiida_atomistic.data.structure.structure


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.structure.StructureData
   aiida_atomistic.data.structure.structure.StructureDataMutable




.. py:class:: StructureData(validate_kinds=True, sites: list[dict] = None, kinds: list[dict] = None, **kwargs)


   Bases: :py:obj:`aiida.orm.nodes.data.Data`, :py:obj:`aiida_atomistic.data.structure.getter_mixin.GetterMixin`

   The base class for all Data nodes.

   AiiDA Data classes are subclasses of Node and must support multiple inheritance.

   Architecture note:
   Calculation plugins are responsible for converting raw output data from simulation codes to Data nodes.
   Nodes are responsible for validating their content (see _validate method).

   .. py:property:: properties


   .. py:attribute:: _mutable
      :value: False



   .. py:method:: from_mutable(mutable_structure, validate_kinds=True)
      :classmethod:


   .. py:method:: to_mutable()


   .. py:method:: get_value()



.. py:class:: StructureDataMutable(validate_kinds=True, sites: list[dict] = None, kinds: list[dict] = None, **kwargs)


   Bases: :py:obj:`aiida_atomistic.data.structure.getter_mixin.GetterMixin`, :py:obj:`aiida_atomistic.data.structure.setter_mixin.SetterMixin`

   .. py:property:: properties


   .. py:attribute:: _mutable
      :value: True
