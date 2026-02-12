:py:mod:`aiida_atomistic.data.structure.hubbard_mixin`
======================================================

.. py:module:: aiida_atomistic.data.structure.hubbard_mixin

.. autoapi-nested-parse::

   Utility class and functions for HubbardStructureData.
   Borrowed and adapted from aiida-quantumespresso



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.hubbard_mixin.HubbardGetterMixin
   aiida_atomistic.data.structure.hubbard_mixin.HubbardSetterMixin




.. py:class:: HubbardGetterMixin


   .. py:method:: get_hubbard_list() -> List[Tuple[int, str, int, str, float, Tuple[int, int, int], str]]

      Return the Hubbard `parameters` as a list of lists.

      The parameters have the following order within each list:
          * atom_index
          * atom_manifold
          * neighbour_index
          * neighbour_manifold
          * value
          * translation
          * hubbard_type



.. py:class:: HubbardSetterMixin


   .. py:method:: set_hubbard_from_list(parameters: List[Tuple[int, str, int, str, float, Tuple[int, int, int], str]], projectors: str = 'ortho-atomic', formulation: str = 'dudarev')

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


   .. py:method:: pop_hubbard_parameters(index: int = -1)

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


   .. py:method:: _get_one_kind_index(kinds: str) -> List[int]

      Return the first site index matching with `kinds`.


   .. py:method:: _get_symbol_indices(symbol: str) -> List[int]

      Return one site index for each kind name matching symbol.
