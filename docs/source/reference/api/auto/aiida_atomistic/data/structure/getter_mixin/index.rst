:py:mod:`aiida_atomistic.data.structure.getter_mixin`
=====================================================

.. py:module:: aiida_atomistic.data.structure.getter_mixin


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.getter_mixin.GetterMixin




Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.getter_mixin.has_ase
   aiida_atomistic.data.structure.getter_mixin.has_pymatgen
   aiida_atomistic.data.structure.getter_mixin._MASS_THRESHOLD
   aiida_atomistic.data.structure.getter_mixin._SUM_THRESHOLD
   aiida_atomistic.data.structure.getter_mixin._DEFAULT_CELL
   aiida_atomistic.data.structure.getter_mixin._valid_symbols
   aiida_atomistic.data.structure.getter_mixin._atomic_masses
   aiida_atomistic.data.structure.getter_mixin._atomic_numbers
   aiida_atomistic.data.structure.getter_mixin._DEFAULT_THRESHOLDS


.. py:data:: has_ase
   :value: True



.. py:data:: has_pymatgen
   :value: True



.. py:data:: _MASS_THRESHOLD
   :value: 0.001



.. py:data:: _SUM_THRESHOLD
   :value: 1e-06



.. py:data:: _DEFAULT_CELL



.. py:data:: _valid_symbols



.. py:data:: _atomic_masses



.. py:data:: _atomic_numbers



.. py:data:: _DEFAULT_THRESHOLDS



.. py:class:: GetterMixin


   Bases: :py:obj:`aiida_atomistic.data.structure.hubbard_mixin.HubbardGetterMixin`

   .. py:property:: cell


   .. py:property:: pbc


   .. py:property:: sites


   .. py:property:: kinds


   .. py:property:: is_alloy


   .. py:property:: has_vacancies


   .. py:property:: formula


   .. py:property:: is_collinear


   .. py:method:: get_supported_properties()
      :staticmethod:

      Get a dictionary of global and site properties that can be set
      for this structure.


   .. py:method:: get_defined_properties()

      Retrieve the defined properties of the structure, categorized into direct, computed, and site-specific properties.

      Args:
          exclude_computed (bool): If False, all properties will be returned, including those computed after the initialization (the pydantic computed fields).
          exclude_defaults (bool): If True, properties with default values will be excluded from the result.


   .. py:method:: get_kind_names()

      Return a list of the kind names defined in this structure.


   .. py:method:: get_kind(kind_name: str = None)

      Return a given kind.


   .. py:method:: from_ase(aseatoms: ASE_ATOMS_TYPE, detect_kinds: bool = False)
      :classmethod:

      Load the structure from a ASE object


   .. py:method:: from_file(filename, format='cif', detect_kinds: bool = False, **kwargs)
      :classmethod:

      Load the structure from a file.


   .. py:method:: from_pymatgen(pymatgen_obj: Union[PYMATGEN_MOLECULE, PYMATGEN_STRUCTURE], detect_kinds: bool = False, **kwargs)
      :classmethod:

      Load the structure from a pymatgen object.

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).


   .. py:method:: _from_pymatgen_molecule(mol: PYMATGEN_MOLECULE, margin=5, detect_kinds: bool = False)
      :classmethod:

      Load the structure from a pymatgen Molecule object.

      :param margin: the margin to be added in all directions of the
          bounding box of the molecule.

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).


   .. py:method:: _from_pymatgen_structure(struct: PYMATGEN_STRUCTURE, detect_kinds: bool = False)
      :classmethod:

      Load the structure from a pymatgen Structure object.

      .. note:: periodic boundary conditions are set to True in all
          three directions.
      .. note:: Requires the pymatgen module (version >= 3.3.5, usage
          of earlier versions may cause errors).

      :raise ValueError: if there are partial occupancies together with spins.


   .. py:method:: generate_kinds(tolerance: Union[dict, float] = 0.001)


   .. py:method:: validate_kinds()


   .. py:method:: to_dict(exclude_kinds=False)

      Convert the structure to a dictionary representation.

      :param detect_kinds: Whether to detect and include the kinds of the structure.
      :type detect_kinds: bool, optional
      :return: The structure as a dictionary.
      :rtype: dict


   .. py:method:: to_kinds_based(tolerance: Union[dict, float] = 0.001)

      Convert the structure to a kinds-based representation.

      :param tolerance: Tolerance for grouping sites into kinds. Can be a float or a dictionary specifying tolerances for specific properties.
      :type tolerance: float or dict, optional
      :return: The structure as a dictionary with kinds.
      :rtype: dict


   .. py:method:: get_cif(converter='ase', store=False, **kwargs)

      Creates :py:class:`aiida.orm.nodes.data.cif.CifData`.

      :param converter: specify the converter. Default 'ase'.
      :param store: If True, intermediate calculation gets stored in the
          AiiDA database for record. Default False.
      :return: :py:class:`aiida.orm.nodes.data.cif.CifData` node.


   .. py:method:: get_description()

      Returns a string with infos retrieved from StructureData node's properties

      :param self: the StructureData node
      :return: retsrt: the description string


   .. py:method:: get_composition(mode='full')

      Returns the chemical composition of this structure as a dictionary,
      where each key is the kind symbol (e.g. H, Li, Ba),
      and each value is the number of occurences of that element in this
      structure.

      :param mode: Specify the mode of the composition to return. Choose from ``full``, ``reduced`` or ``fractional``.
          For example, given the structure with formula Ba2Zr2O6, the various modes operate as follows.
          ``full``: The default, the counts are left unnnormalized.
          ``reduced``: The counts are renormalized to the greatest common denominator.
          ``fractional``: The counts are renormalized such that the sum equals 1.

      :returns: a dictionary with the composition


   .. py:method:: to_ase()

      Get the ASE object.
      Requires to be able to import ase.

      :return: an ASE object corresponding to this
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
      object.

      .. note:: If any site is an alloy or has vacancies, a ValueError
          is raised (from the site.to_ase() routine).


   .. py:method:: to_pymatgen(**kwargs)

      Get pymatgen object. Returns pymatgen Structure for structures with periodic boundary conditions
      (in 1D, 2D, 3D) and Molecule otherwise.
      :param add_spin: True to add the spins to the pymatgen structure.
      Default is False (no spin added).

      .. note:: The spins are set according to the following rule:

          * if the kind name ends with 1 -> spin=+1

          * if the kind name ends with 2 -> spin=-1

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).


   .. py:method:: to_file(filename=None, format='cif')

      Writes the structure to a file.

      Args:
          filename (_type_, optional): defaults to None.
          format (str, optional): defaults to "cif".

      Raises:
          ValueError: should provide a filename different from None.


   .. py:method:: get_pymatgen_structure(**kwargs)

      Get the pymatgen Structure object with any PBC, provided the cell is not singular.
      :param add_spin: True to add the spins to the pymatgen structure.
      Default is False (no spin added).

      .. note:: The spins are set according to the following rule:

          * if the kind name ends with 1 -> spin=+1

          * if the kind name ends with 2 -> spin=-1

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).

      :return: a pymatgen Structure object corresponding to this
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
      object.
      :raise ValueError: if the cell is singular, e.g. when it has not been set.
          Use `get_pymatgen_molecule` instead, or set a proper cell.


   .. py:method:: get_pymatgen_molecule()

      Get the pymatgen Molecule object.

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).

      :return: a pymatgen Molecule object corresponding to this
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
      object.


   .. py:method:: _prepare_xsf(main_file_name='')

      Write the given structure to a string of format XSF (for XCrySDen).


   .. py:method:: _prepare_cif(main_file_name='')

      Write the given structure to a string of format CIF.


   .. py:method:: _prepare_chemdoodle(main_file_name='')

      Write the given structure to a string of format required by ChemDoodle.


   .. py:method:: _prepare_xyz(main_file_name='')

      Write the given structure to a string of format XYZ.


   .. py:method:: _parse_xyz(inputstring)

      Read the structure from a string of format XYZ.


   .. py:method:: _adjust_default_cell(vacuum_factor=1.0, vacuum_addition=10.0, pbc=(False, False, False))

      If the structure was imported from an xyz file, it lacks a cell.
      This method will adjust the cell


   .. py:method:: _get_object_phonopyatoms()

      Converts StructureData to PhonopyAtoms

      :return: a PhonopyAtoms object


   .. py:method:: _get_object_ase()

      Converts
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
      to ase.Atoms

      :return: an ase.Atoms object


   .. py:method:: _get_object_pymatgen(**kwargs)

      Converts
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
      to pymatgen object

      :return: a pymatgen Structure for structures with periodic boundary
          conditions (in three dimensions) and Molecule otherwise

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).


   .. py:method:: _get_object_pymatgen_structure(**kwargs)

      Converts
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
      to pymatgen Structure object
      :param add_spin: True to add the spins to the pymatgen structure.
      Default is False (no spin added).

      .. note:: The spins are set according to the following rule:

          * if the kind name ends with 1 -> spin=+1

          * if the kind name ends with 2 -> spin=-1

      :return: a pymatgen Structure object corresponding to this
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        object
      :raise ValueError: if the cell is not set (i.e. is the default one);
        if there are partial occupancies together with spins
        (defined by kind names ending with '1' or '2').

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors)


   .. py:method:: _get_object_pymatgen_molecule(**kwargs)

      Converts
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
      to pymatgen Molecule object

      :return: a pymatgen Molecule object corresponding to this
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        object.

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors)


   .. py:method:: _get_dimensionality()

      Return the dimensionality of the structure and its length/surface/volume.

      Zero-dimensional structures are assigned "volume" 0.

      :return: returns a dictionary with keys "dim" (dimensionality integer), "label" (dimensionality label)
          and "value" (numerical length/surface/volume).


   .. py:method:: _validate_dimensionality()

      Check whether the given pbc and cell vectors are consistent.


   .. py:method:: get_symbols_set()

      Return the set of unique chemical symbols in the structure.


   .. py:method:: __len__()
