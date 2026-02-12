:py:mod:`aiida_atomistic.data.structure.models`
===============================================

.. py:module:: aiida_atomistic.data.structure.models


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.models.StructureBaseModel
   aiida_atomistic.data.structure.models.MutableStructureModel
   aiida_atomistic.data.structure.models.ImmutableStructureModel
   aiida_atomistic.data.structure.models.MutableStructureModel
   aiida_atomistic.data.structure.models.ImmutableStructureModel




.. py:class:: StructureBaseModel(/, **data: Any)


   Bases: :py:obj:`pydantic.BaseModel`

   A base model representing a structure in atomistic simulations.

   Attributes:
       pbc (Optional[List[bool]]): Periodic boundary conditions in the x, y, and z directions.
       cell (Optional[List[List[float]]]): The cell vectors defining the unit cell of the structure.

   .. py:property:: cell_volume
      :type: float

      Compute the volume of the unit cell.

      Returns:
          float: The volume of the unit cell in cubic Angstroms.


   .. py:property:: dimensionality
      :type: dict

      Determine the dimensionality of the structure.

      Returns:
          dict: A dictionary indicating the dimensionality of the structure.


   .. py:property:: formula
      :type: str

      Get the chemical formula of the structure.

      Returns:
          str: The chemical formula of the structure.


   .. py:property:: is_alloy
      :type: dict

      Computed field to determine if the structure is an alloy.


   .. py:property:: has_vacancies
      :type: bool

      Computed field to determine if the structure has vacancies.


   .. py:property:: positions
      :type: numpy.ndarray

      Return the positions of all sites in the structure as a numpy array.

      Returns:
          np.ndarray: An array of shape (N, 3) where N is the number of sites.


   .. py:property:: kind_names
      :type: List[str]

      Return the list of kind names for all sites in the structure.

      Returns:
          List[str]: A list of kind names corresponding to each site.


   .. py:property:: symbols
      :type: List[str]

      Return the list of chemical symbols for all sites in the structure.

      Returns:
          List[str]: A list of chemical symbols corresponding to each site.


   .. py:property:: masses
      :type: numpy.ndarray

      Return the masses of all sites in the structure as a numpy array.

      Returns:
          np.ndarray: An array of masses corresponding to each site.


   .. py:property:: charges
      :type: numpy.ndarray

      Return the charges of all sites in the structure as a numpy array.

      Returns:
          np.ndarray: An array of charges corresponding to each site.


   .. py:property:: magmoms
      :type: numpy.ndarray

      Return the magnetic moments of all sites in the structure as a numpy array.

      Returns:
          np.ndarray: An array of magnetic moments corresponding to each site.


   .. py:property:: magnetizations
      :type: numpy.ndarray

      Return the magnetizations of all sites in the structure as a numpy array.

      Returns:
          np.ndarray: An array of magnetizations corresponding to each site.


   .. py:property:: weights
      :type: List[Tuple[float, Ellipsis]]

      Return the weights of all sites in the structure as a list of tuples.

      Returns:
          List[Tuple[float, ...]]: A list of weight tuples corresponding to each site.


   .. py:property:: kinds
      :type: list[aiida_atomistic.data.structure.kind.Kind]

      Return the reduced set of kinds, grouping sites that share all properties except positions and site_indices.


   .. py:property:: max_charge
      :type: Optional[float]

      Maximum charge value across all sites.


   .. py:property:: min_charge
      :type: Optional[float]

      Minimum charge value across all sites.


   .. py:property:: max_magmom
      :type: Optional[float]

      Maximum magnetic moment magnitude across all sites.


   .. py:property:: min_magmom
      :type: Optional[float]

      Minimum magnetic moment magnitude across all sites.


   .. py:property:: max_magnetization
      :type: Optional[float]

      Maximum magnetization value across all sites.


   .. py:property:: min_magnetization
      :type: Optional[float]

      Minimum magnetization value across all sites.


   .. py:property:: n_sites
      :type: int

      Total number of sites in the structure.


   .. py:attribute:: _mutable
      :type: ClassVar[bool]
      :value: True



   .. py:attribute:: pbc
      :type: list[bool]



   .. py:attribute:: cell
      :type: aiida_atomistic.data.structure.site.NumpyArray



   .. py:attribute:: sites
      :type: list[aiida_atomistic.data.structure.site.Site]



   .. py:attribute:: tot_magnetization
      :type: Optional[float]



   .. py:attribute:: tot_charge
      :type: Optional[float]



   .. py:attribute:: hubbard
      :type: Optional[aiida_quantumespresso.common.hubbard.Hubbard]



   .. py:attribute:: custom
      :type: Optional[dict]



   .. py:attribute:: model_config



   .. py:method:: validate_cell_shape(v)
      :classmethod:

      Ensure cell is always a 3x3 array.


   .. py:method:: check_minimal_requirements(data)

      Validate the minimal requirements of the structure.

      Args:
          data (dict): The input data for the structure. This is automatically passed by pydantic.

      Returns:
          dict: The validated input data.

      Raises:
          ValueError: If the structure does not meet the minimal requirements.


   .. py:method:: validate_sites(v)

      Validate the list of sites.


   .. py:method:: freeze_sites(v)

      Freeze the list of sites if the structure is immutable.


   .. py:method:: freeze_custom(v)

      Freeze the list of sites if the structure is immutable.


   .. py:method:: __repr__() -> str

      Return repr(self).


   .. py:method:: __str__()

      Return str(self).



.. py:class:: MutableStructureModel(/, **data: Any)


   Bases: :py:obj:`StructureBaseModel`

   A mutable structure model that extends the StructureBaseModel class.

   Attributes:
       _mutable (bool): Flag indicating whether the structure is mutable or not.
       sites (List[Site]): List of immutable sites in the structure.

   .. py:attribute:: _mutable
      :value: True




.. py:class:: ImmutableStructureModel(/, **data: Any)


   Bases: :py:obj:`StructureBaseModel`

   A class representing an immutable structure model.

   This class inherits from `StructureBaseModel` and provides additional functionality for handling immutable structures.

   Attributes:
       _mutable (bool): Flag indicating whether the structure is mutable or not.
       sites (List[Site]): List of immutable sites in the structure.

   Config:
       from_attributes (bool): Flag indicating whether to load attributes from the input data.
       frozen (bool): Flag indicating whether the model is frozen or not.
       arbitrary_types_allowed (bool): Flag indicating whether arbitrary types are allowed or not.

   .. py:attribute:: _mutable
      :value: False



   .. py:attribute:: sites
      :type: Optional[list[aiida_atomistic.data.structure.site.FrozenSite]]



   .. py:attribute:: model_config



   .. py:method:: freeze_pbc(v)
      :classmethod:

      Freeze the pbc list to make it immutable.


   .. py:method:: __setattr__(key, value)

      Implement setattr(self, name, value).



.. py:class:: MutableStructureModel(/, **data: Any)


   Bases: :py:obj:`StructureBaseModel`

   A mutable structure model that extends the StructureBaseModel class.

   Attributes:
       _mutable (bool): Flag indicating whether the structure is mutable or not.
       sites (List[Site]): List of immutable sites in the structure.

   .. py:attribute:: _mutable
      :value: True




.. py:class:: ImmutableStructureModel(/, **data: Any)


   Bases: :py:obj:`StructureBaseModel`

   A class representing an immutable structure model.

   This class inherits from `StructureBaseModel` and provides additional functionality for handling immutable structures.

   Attributes:
       _mutable (bool): Flag indicating whether the structure is mutable or not.
       sites (List[Site]): List of immutable sites in the structure.

   Config:
       from_attributes (bool): Flag indicating whether to load attributes from the input data.
       frozen (bool): Flag indicating whether the model is frozen or not.
       arbitrary_types_allowed (bool): Flag indicating whether arbitrary types are allowed or not.

   .. py:attribute:: _mutable
      :value: False



   .. py:attribute:: sites
      :type: Optional[list[aiida_atomistic.data.structure.site.FrozenSite]]



   .. py:attribute:: model_config



   .. py:method:: freeze_pbc(v)
      :classmethod:

      Freeze the pbc list to make it immutable.


   .. py:method:: __setattr__(key, value)

      Implement setattr(self, name, value).
