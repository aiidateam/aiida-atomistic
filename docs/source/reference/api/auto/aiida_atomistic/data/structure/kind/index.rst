:py:mod:`aiida_atomistic.data.structure.kind`
=============================================

.. py:module:: aiida_atomistic.data.structure.kind


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.kind.Kind




.. py:class:: Kind(/, **data: Any)


   Bases: :py:obj:`aiida_atomistic.data.structure.site.FrozenSite`

   This class contains the core information about a given kind of the system.



   .. py:property:: name
      :type: str

      Return the name of the kind. This is an alias of `kind_name`.


   .. py:attribute:: _mutable
      :type: ClassVar[bool]
      :value: False



   .. py:attribute:: position
      :type: Union[numpy.ndarray[float]]



   .. py:attribute:: positions
      :type: Union[numpy.ndarray[float], list[float]]



   .. py:attribute:: site_indices
      :type: Optional[List[int]]
