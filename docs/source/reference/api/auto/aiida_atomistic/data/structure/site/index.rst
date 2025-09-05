:py:mod:`aiida_atomistic.data.structure.site`
=============================================

.. py:module:: aiida_atomistic.data.structure.site


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.site.FrozenList
   aiida_atomistic.data.structure.site.Site
   aiida_atomistic.data.structure.site.FrozenSite



Functions
~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.site.freeze_nested



.. py:function:: freeze_nested(obj)

   Recursively freezes a nested dictionary or list by converting it into an immutable object.

   Args:
       obj (dict or list): The nested dictionary or list to be frozen.

   Returns:
       AttributesFrozendict or FrozenList: The frozen version of the input object.



.. py:class:: FrozenList


   Bases: :py:obj:`list`

   A subclass of list that represents an immutable list.

   This class overrides the __setitem__ method to raise a ValueError
   when attempting to modify the list.

   Usage:
   >>> my_list = FrozenList([1, 2, 3])
   >>> my_list[0] = 4
   ValueError: This list is immutable...

   .. py:method:: __setitem__(index, value)

      Set self[key] to value.



.. py:class:: Site(/, **data: Any)


   Bases: :py:obj:`pydantic.BaseModel`

   This class contains the core information about a given site of the system.

   It can be a single atom, or an alloy, or even contain vacancies.


   .. py:property:: is_alloy

      Return whether the Site is an alloy, i.e. contains more than one element

      :return: boolean, True if the kind has more than one element, False otherwise.


   .. py:property:: alloy_list

      Return the list of elements in the given site which is defined as an alloy



   .. py:property:: has_vacancies

      Return whether the Structure contains vacancies, i.e. when the sum of the weight is less than one.

      .. note:: the property uses the internal variable `_SUM_THRESHOLD` as a threshold.

      :return: boolean, True if the sum of the weight is less than one, False otherwise


   .. py:attribute:: _mutable
      :type: ClassVar[bool]
      :value: True



   .. py:attribute:: model_config



   .. py:attribute:: symbol
      :type: Union[str, List[str]]



   .. py:attribute:: position
      :type: Union[numpy.ndarray[float]]



   .. py:attribute:: mass
      :type: Optional[float]



   .. py:attribute:: charge
      :type: Optional[float]



   .. py:attribute:: magmom
      :type: Optional[numpy.ndarray[float]]



   .. py:attribute:: magnetization
      :type: Optional[float]



   .. py:attribute:: weight
      :type: Optional[Tuple[float, Ellipsis]]



   .. py:attribute:: kind_name
      :type: Optional[str]



   .. py:method:: ensure_numpy_array(v)
      :classmethod:

      We want to ensure that the input is a numpy array.


   .. py:method:: check_minimal_requirements(data)


   .. py:method:: from_ase_atom(aseatom: Optional[ase.Atom] = None, **kwargs) -> dict
      :classmethod:

      Convert an ASE atom or dictionary to a dictionary object which the correct format to describe a Site.


   .. py:method:: update(**new_data)

      Update the attributes of the SiteCore instance with new values.

      :param new_data: keyword arguments representing the attributes to be updated


   .. py:method:: get_magmom_coord(coord='spherical')

      Get magnetic moment in given coordinate.

      :return: spherical theta and phi in unit rad
              cartesian x y and z in unit ang


   .. py:method:: set_automatic_kind_name(tag=None)

      Set the type to a string obtained with the symbol appended one
      after the other, without spaces, in alphabetical order;
      if the site has a vacancy, a X is appended at the end too.

      :param tag: optional tag to be appended to the kind name


   .. py:method:: to_ase()

      Return a ase.Atom object for this site.

      :param kind_name: the list of kind_name from the StructureData object.
      :return: ase.Atom object representing this site
      :raises ValueError: if any site is an alloy or has vacancies



.. py:class:: FrozenSite(/, **data: Any)


   Bases: :py:obj:`Site`

   This class contains the core information about a given site of the system.

   It can be a single atom, or an alloy, or even contain vacancies.


   .. py:attribute:: _mutable
      :type: ClassVar[bool]
      :value: False



   .. py:attribute:: model_config
