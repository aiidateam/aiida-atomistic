:py:mod:`hubbard`
=================

.. py:module:: hubbard

.. autoapi-nested-parse::

   Utility class and functions for HubbardStructureData.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   hubbard.HubbardParameters
   hubbard.Hubbard




.. py:class:: HubbardParameters


   Bases: :py:obj:`aiida_atomistic.data.structure.property.BaseModel`

   Class for describing onsite and intersite Hubbard interaction parameters.

   .. note: allowed manifold formats are:
           * {N}{L} (2 characters)
           * {N1}{L1}-{N2}{L2} (5 characters)

       N = quantum number (1,2,3,...); L = orbital letter (s,p,d,f,g,h)

   .. py:attribute:: _hubbard_filename
      :value: 'hubbard.json'

      

   .. py:attribute:: atom_index
      :type: conint(strict=True, ge=0)

      Atom index in the abstract structure.


   .. py:attribute:: atom_manifold
      :type: constr(strip_whitespace=True, to_lower=True, min_length=2, max_length=5)

      Atom manifold (syntax is `3d`, `3d-2p`).


   .. py:attribute:: neighbour_index
      :type: conint(strict=True, ge=0)

      Neighbour index in the abstract structure.


   .. py:attribute:: neighbour_manifold
      :type: constr(strip_whitespace=True, to_lower=True, min_length=2, max_length=5)

      Atom manifold (syntax is `3d`, `3d-2p`).


   .. py:attribute:: translation
      :type: Tuple[conint(strict=True), conint(strict=True), conint(strict=True)]

      Translation vector referring to the neighbour atom, (3,) shape list of ints.


   .. py:attribute:: value
      :type: float

      Value of the Hubbard parameter, expessed in eV.


   .. py:attribute:: hubbard_type
      :type: Literal[Ueff, U, V, J, B, E2, E3]

      Type of the Hubbard parameters used (`Ueff`, `U`, `V`, `J`, `B`, `E2`, `E3`).


   .. py:method:: check_manifolds(value)

      Check the validity of the manifold input.

      Allowed formats are:
          * {N}{L} (2 characters)
          * {N1}{L1}-{N2}{L2} (5 characters)

      N = quantum number (1,2,3,...); L = orbital letter (s,p,d,f,g,h)


   .. py:method:: to_tuple() -> Tuple[int, str, int, str, float, Tuple[int, int, int], str]

      Return the parameters as a tuple.

      The parameters have the following order:
          * atom_index
          * atom_manifold
          * neighbour_index
          * neighbour_manifold
          * value
          * translationr
          * hubbard_type


   .. py:method:: from_tuple(hubbard_parameters: Tuple[int, str, int, str, float, Tuple[int, int, int], str])
      :staticmethod:

      Return a ``HubbardParameters``  instance from a list.

      The parameters within the list must have the following order:
          * atom_index
          * atom_manifold
          * neighbour_index
          * neighbour_manifold
          * value
          * translation
          * hubbard_type


   .. py:method:: from_list(hubbard_list=List)
      :staticmethod:



.. py:class:: Hubbard


   Bases: :py:obj:`aiida_atomistic.data.structure.property.BaseProperty`

   Class for complete description of Hubbard interactions.

   .. py:attribute:: parameters
      :type: aiida_atomistic.data.structure.property.List[HubbardParameters]

      List of :class:`~aiida_quantumespresso.common.hubbard.HubbardParameters`.


   .. py:attribute:: projectors
      :type: Literal[atomic, ortho-atomic, norm-atomic, wannier-functions, pseudo-potentials]

      Name of the projectors used. Allowed values are:
      'atomic', 'ortho-atomic', 'norm-atomic', 'wannier-functions', 'pseudo-potentials'.


   .. py:attribute:: formulation
      :type: Literal[dudarev, liechtenstein]

      Hubbard formulation used. Allowed values are: 'dudarev', `liechtenstein`.


   .. py:method:: to_list() -> aiida_atomistic.data.structure.property.List[Tuple[int, str, int, str, float, Tuple[int, int, int], str]]

      Return the Hubbard `parameters` as a list of lists.

      The parameters have the following order within each list:
          * atom_index
          * atom_manifold
          * neighbour_index
          * neighbour_manifold
          * value
          * translation
          * hubbard_type


   .. py:method:: from_list(parameters: aiida_atomistic.data.structure.property.List[Tuple[int, str, int, str, float, Tuple[int, int, int], str]], projectors: str = 'ortho-atomic', formulation: str = 'dudarev')

      Return a :meth:`~aiida_quantumespresso.common.hubbard.Hubbard` instance from a list of tuples.

      Each list must contain the hubbard parameters in the following order:
          * atom_index
          * atom_manifold
          * neighbour_index
          * neighbour_manifold
          * value
          * translation
          * hubbard_type


   .. py:method:: append_hubbard_parameter(atom_index: int, atom_manifold: str, neighbour_index: int, neighbour_manifold: str, value: float, translation: Tuple[int, int, int] = None, hubbard_type: str = 'Ueff')

      Append a :class:`~aiida_quantumespresso.common.hubbard.HubbardParameters`.

      :param atom_index: atom index in unitcell
      :param atom_manifold: atomic manifold (e.g. 3d, 3d-2p)
      :param neighbour_index: neighbouring atom index in unitcell
      :param neighbour_manifold: neighbour manifold (e.g. 3d, 3d-2p)
      :param value: value of the Hubbard parameter, in eV
      :param translation: (3,) list of ints, describing the translation vector
          associated with the neighbour atom, defaults to None
      :param hubbard_type: hubbard type (U, V, J, ...), defaults to 'Ueff'
          (see :class:`~aiida_quantumespresso.common.hubbard.Hubbard` for full allowed values)


   .. py:method:: pop_hubbard_parameters(index: int)

      Pop Hubbard parameters in the list.

      :param index: index of the Hubbard parameters to pop


   .. py:method:: clear_hubbard_parameters()

      Clear all the Hubbard parameters.


   .. py:method:: initialize_intersites_hubbard(atom_name: str, atom_manifold: str, neighbour_name: str, neighbour_manifold: str, value: float = 1e-08, hubbard_type: str = 'V', use_kinds: bool = True)

      Initialize and append intersite Hubbard values between an atom and its neighbour(s).

      .. note:: this only initialize the value between the first neighbour. In case
          `use_kinds` is False, all the possible combination of couples having
          kind  name equal to symbol are initialized.

      :param atom_name: atom name in unitcell
      :param atom_manifold: atomic manifold (e.g. 3d, 3d-2p)
      :param neighbour_index: neighbouring atom name in unitcell
      :param neighbour_manifold: neighbour manifold (e.g. 3d, 3d-2p)
      :param value: value of the Hubbard parameter, in eV
      :param hubbard_type: hubbard type (U, V, J, ...), defaults to 'V'
          (see :class:`~aiida_quantumespresso.common.hubbard.Hubbard` for full allowed values)
      :param use_kinds: whether to use kinds for initializing the parameters; when False, it
          initializes all the ``Kinds`` matching the ``atom_name``


   .. py:method:: initialize_onsites_hubbard(atom_name: str, atom_manifold: str, value: float = 1e-08, hubbard_type: str = 'Ueff', use_kinds: bool = True)

      Initialize and append onsite Hubbard values of atoms with specific name.

      :param atom_name: atom name in unitcell
      :param atom_manifold: atomic manifold (e.g. 3d, 3d-2p)
      :param value: value of the Hubbard parameter, in eV
      :param hubbard_type: hubbard type (U, J, ...), defaults to 'Ueff'
          (see :class:`~aiida_quantumespresso.common.hubbard.Hubbard` for full allowed values)
      :param use_kinds: whether to use kinds for initializing the parameters; when False, it
          initializes all the ``Kinds`` matching the ``atom_name``


   .. py:method:: _get_one_kind_index(kind_name: str) -> aiida_atomistic.data.structure.property.List[int]

      Return the first site index matching with `kind_name`.


   .. py:method:: _get_symbol_indices(symbol: str) -> aiida_atomistic.data.structure.property.List[int]

      Return one site index for each kind name matching symbol.



