:py:mod:`hubbard_qe_utils`
==========================

.. py:module:: hubbard_qe_utils

.. autoapi-nested-parse::

   Utility class for handling the :class:`aiida_atomistic.data.structure.structure.StructureData` if
   hubbard property is set and used in the aiida-quantumespresso plugin.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   hubbard_qe_utils.HubbardUtils



Functions
~~~~~~~~~

.. autoapisummary::

   hubbard_qe_utils.get_supercell_atomic_index
   hubbard_qe_utils.get_index_and_translation
   hubbard_qe_utils.get_hubbard_indices
   hubbard_qe_utils.is_intersite_hubbard



.. py:class:: HubbardUtils(hubbard_structure: StructureData)


   Utility class for handling `Hubbard` property for QuantumESPRESSO.

   .. py:property:: hubbard_structure
      :type: StructureData

      Return the StructureData.


   .. py:method:: get_hubbard_card() -> str

      Return QuantumESPRESSO `HUBBARD` input card for `pw.x`.


   .. py:method:: parse_hubbard_dat(filepath: Union[str, os.PathLike])

      Parse the `HUBBARD.dat` of QuantumESPRESSO file associated to the current structure.

      This function is needed for parsing the HUBBARD.dat file generated in a `hp.x` calculation.

      .. note:: overrides current Hubbard information.

      :param filepath: the filepath of the *HUBBARD.dat* to parse


   .. py:method:: get_hubbard_file() -> str

      Return QuantumESPRESSO ``parameters.in`` data for ``pw.x```.


   .. py:method:: reorder_atoms()

      Reorder the atoms with with the kinds in the right order necessary for an ``hp.x`` calculation.

      An ``HpCalculation`` which restarts from a completed ``PwCalculation``, requires that the all
      Hubbard atoms appear first in  the atomic positions card of the ``PwCalculation`` input file.
      This order is based on the order of the kinds in the structure.
      So a suitable structure has all Hubbard kinds in the begining of kinds list.

      .. note:: overrides current ``HubbardStructureData``


   .. py:method:: is_to_reorder() -> bool

      Return whether the atoms should be reordered for an ``hp.x`` calculation.


   .. py:method:: get_hubbard_for_supercell(supercell: StructureData, thr: float = 0.001) -> StructureData

      Return the ``StructureData`` for a supercell.

      .. note:: the two structure need to be commensurate (no rigid rotations)

      .. warning:: **always check** that the energy calculation of a pristine supercell
          structure obtained through this method is the same as the unitcell (within numerical noise)

      :returns: a new ``StructureData`` with all the mapped Hubbard parameters



.. py:function:: get_supercell_atomic_index(index: int, num_sites: int, translation: List[Tuple[int, int, int]]) -> int

   Return the atomic index in 3x3x3 supercell.

   :param index: atomic index in unit cell
   :param num_sites: number of sites in structure
   :param translation: (3,) shape list of int referring to the translated atom in the 3x3x3 supercell

   :returns: atomic index in supercell standardized with the QuantumESPRESSO loop


.. py:function:: get_index_and_translation(index: int, num_sites: int) -> Tuple[int, List[Tuple[int, int, int]]]

   Return the atomic index in unitcell and the associated translation from a 3x3x3 QuantumESPRESSO supercell index.

   :param index: atomic index
   :param num_sites: number of sites in structure
   :returns: tuple (index, (3,) shape list of ints)


.. py:function:: get_hubbard_indices(hubbard) -> List[int]

   Return the set list of Hubbard indices.


.. py:function:: is_intersite_hubbard(hubbard) -> bool

   Return whether `Hubbard` contains intersite interactions (+V).


