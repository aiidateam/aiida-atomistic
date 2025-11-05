:py:mod:`aiida_atomistic.data.structure.hubbard_qe_utils`
=========================================================

.. py:module:: aiida_atomistic.data.structure.hubbard_qe_utils

.. autoapi-nested-parse::

   Utility class for handling the :class:`aiida_quantumespresso.data.hubbard_structure.HubbardStructureData`.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.hubbard_qe_utils.HubbardUtils



Functions
~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.hubbard_qe_utils.get_supercell_atomic_index
   aiida_atomistic.data.structure.hubbard_qe_utils.get_index_and_translation
   aiida_atomistic.data.structure.hubbard_qe_utils.get_hubbard_indices
   aiida_atomistic.data.structure.hubbard_qe_utils.is_intersite_hubbard



.. py:class:: HubbardUtils(hubbard_structure: Union[aiida_atomistic.data.structure.structure.StructureData, aiida_atomistic.data.structure.structure.StructureBuilder])


   Utility class for handling `HubbardStructureData` for QuantumESPRESSO.

   .. py:property:: hubbard_structure
      :type: Union[aiida_atomistic.data.structure.structure.StructureData, aiida_atomistic.data.structure.structure.StructureBuilder]

      Return the HubbardStructureData.


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


   .. py:method:: get_hubbard_for_supercell(supercell: aiida_atomistic.data.structure.structure.StructureBuilder, thr: float = 0.001, mutable=True) -> Union[aiida_atomistic.data.structure.structure.StructureData, aiida_atomistic.data.structure.structure.StructureBuilder]

      Return the ``HubbbardLegacyStructureData`` for a supercell.

      .. note:: the two structure need to be commensurate (no rigid rotations)

      .. warning:: **always check** that the energy calculation of a pristine supercell
          structure obtained through this method is the same as the unitcell (within numerical noise)

      :returns: a new ``HubbbardLegacyStructureData`` with all the mapped Hubbard parameters



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


.. py:function:: get_hubbard_indices(hubbard: aiida_quantumespresso.common.hubbard.Hubbard) -> List[int]

   Return the set list of Hubbard indices.


.. py:function:: is_intersite_hubbard(hubbard: aiida_quantumespresso.common.hubbard.Hubbard) -> bool

   Return whether `Hubbard` contains intersite interactions (+V).
