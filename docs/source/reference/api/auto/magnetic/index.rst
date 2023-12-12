:py:mod:`magnetic`
==================

.. py:module:: magnetic


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   magnetic.Magnetization



Functions
~~~~~~~~~

.. autoapisummary::

   magnetic.transform_moments
   magnetic.create_magnetic_configuration
   magnetic.make_collinear_getmag_kind



.. py:class:: Magnetization


   Bases: :py:obj:`aiida_atomistic.data.structure.property.BaseProperty`

   .. py:attribute:: moments
      :type: aiida_atomistic.data.structure.property.List[Tuple[float, float, float]]

      

   .. py:attribute:: collinear_kind_moments
      :type: Dict[str, float]

      

   .. py:attribute:: units
      :type: Literal[Bohr_magneton]
      :value: 'Bohr_magneton'

      

   .. py:method:: set_from_components(magnetic_moment_per_site: aiida_atomistic.data.structure.property.List[float] = None, magnetic_moment_per_kind: Dict[str, float] = None, coordinates: Literal[cartesian, spherical, collinear] = 'cartesian', use_kinds: bool = True, atol: float = 0.5, ztol: float = 0.49)

      Create a new magnetic configuration from the given structure based on a list of magnetic moments per site.
      Updates 
          -   the structure.magnetization property and provides both 
              moments and collinear_kind_moments (if kind_base=True. 
              This is a dict kind->magn, magn being a float).
          -   the kinds, if kind_base=True.

      :param structure: a `StructureData` instance.
      :param magnetic_moment_per_site: list of magnetic moments for each site in the structure. Can be both 3D arrays or floats (collinear).
      :param atol: the absolute tolerance on determining if two sites have the same magnetic moment.
      :param ztol: threshold for considering a kind to have non-zero magnetic moment.




.. py:function:: transform_moments(moments, initial, final)

   Translate moments from one system to another.
       


.. py:function:: create_magnetic_configuration(structure, magnetic_moment_per_site, atol: float = 0.5, ztol: float = 0.49)

   Create a new magnetic configuration from the given structure based on a list of magnetic moments per site.

   To create the new list of kinds, the algorithm loops over all the elements in the structure and makes a list of the
   sites with that element and their corresponding magnetic moment. Next, it splits this list in three lists:

   * Zero magnetic moments: Any site that has an absolute magnetic moment lower than ``ztol``
   * Positive magnetic moments
   * Negative magnetic moments

   The algorithm then sorts the positive and negative lists from large to small absolute value, and loops over each of
   list. New magnetic kinds will be created when the absolute difference between the magnetic moment of the current
   kind and the site exceeds ``atol``.

   The positive and negative magnetic moments are handled separately to avoid assigning two sites with opposite signs
   in their magnetic moment to the same kind and make sure that each kind has the correct magnetic moment, i.e. the
   largest magnetic moment in absolute value of the sites corresponding to that kind.

   .. important:: the function currently does not support alloys.

   :param structure: a `StructureData` instance.
   :param magnetic_moment_per_site: list of magnetic moments for each site in the structure.
   :param atol: the absolute tolerance on determining if two sites have the same magnetic moment.
   :param ztol: threshold for considering a kind to have non-zero magnetic moment.


.. py:function:: make_collinear_getmag_kind(structure, magnetic_moment_per_site: aiida_atomistic.data.structure.property.List[float], coordinates: Literal[cartesian, spherical, collinear] = 'cartesian', half=False, atol: float = 0.5, ztol: float = 0.49)

   This calls the 'get_collinear_mag_kindname' utility function.
   It takes the provided magnetic, make it collinear and then with
   assign kind_name property for each atom site relevant
   spin polarized calculation.

   Returns: Structure data and dictionary of pw starting magnetization card.


