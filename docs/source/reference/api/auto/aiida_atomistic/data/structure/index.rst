:py:mod:`aiida_atomistic.data.structure`
========================================

.. py:module:: aiida_atomistic.data.structure

.. autoapi-nested-parse::

   aiida_atomistic

   AiiDA plugin which contains data and methods for atomistic simulations



Submodules
----------
.. toctree::
   :titlesonly:
   :maxdepth: 1

   constants/index.rst
   getter_mixin/index.rst
   hubbard_mixin/index.rst
   hubbard_qe_utils/index.rst
   kind/index.rst
   models/index.rst
   setter_mixin/index.rst
   site/index.rst
   structure/index.rst
   utils/index.rst


Package Contents
----------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.StructureData
   aiida_atomistic.data.structure.StructureBuilder




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



   .. py:attribute:: _model



   .. py:method:: from_builder(mutable_structure, validate_kinds=True)
      :classmethod:


   .. py:method:: to_mutable()


   .. py:method:: get_value()


   .. py:method:: __repr__() -> str

      Return a concise string representation of the structure.


   .. py:method:: __str__() -> str

      Return a string representation of the structure for print().



.. py:class:: StructureBuilder(validate_kinds=True, sites: list[dict] = None, kinds: list[dict] = None, **kwargs)


   Bases: :py:obj:`aiida_atomistic.data.structure.getter_mixin.GetterMixin`, :py:obj:`aiida_atomistic.data.structure.setter_mixin.SetterMixin`

   .. py:property:: properties


   .. py:attribute:: _mutable
      :value: True



   .. py:attribute:: _model



   .. py:method:: __repr__() -> str

      Return a concise string representation of the structure.


   .. py:method:: __str__() -> str

      Return a string representation of the structure for print().
