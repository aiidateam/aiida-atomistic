:py:mod:`structure`
===================

.. py:module:: structure

.. autoapi-nested-parse::

   This module defines the classes for structures and all related
   functions to operate on them.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   structure.StructureData
   structure.Kind
   structure.Site




.. py:class:: StructureData(cell=None, pbc=None, ase=None, pymatgen=None, pymatgen_structure=None, pymatgen_molecule=None, **kwargs)


   Bases: :py:obj:`aiida_atomistic.data.structure.property.HasPropertyMixin`, :py:obj:`aiida_atomistic.data.structure.property.Data`

   This class contains the information about a given structure, i.e. a
   collection of sites together with a cell, the
   boundary conditions (whether they are periodic or not) and other
   related useful information.

   .. py:property:: sites

      Returns a list of sites.


   .. py:property:: kinds

      Returns a list of kinds.


   .. py:property:: cell

      Returns the cell shape.

      :return: a 3x3 list of lists.


   .. py:property:: pbc

      Get the periodic boundary conditions.

      :return: a tuple of three booleans, each one tells if there are periodic
          boundary conditions for the i-th real-space direction (i=1,2,3)


   .. py:property:: cell_lengths

      Get the lengths of cell lattice vectors in angstroms.


   .. py:property:: cell_angles

      Get the angles between the cell lattice vectors in degrees.


   .. py:property:: is_alloy

      Return whether the structure contains any alloy kinds.

      :return: a boolean, True if at least one kind is an alloy


   .. py:property:: has_vacancies

      Return whether the structure has vacancies in the structure.

      :return: a boolean, True if at least one kind has a vacancy


   .. py:attribute:: _set_incompatibilities
      :value: [('ase', 'cell'), ('ase', 'pbc'), ('ase', 'pymatgen'), ('ase', 'pymatgen_molecule'), ('ase',...

      

   .. py:attribute:: _dimensionality_label

      

   .. py:attribute:: _internal_kind_tags

      

   .. py:attribute:: magnetization
      :type: aiida_atomistic.data.structure.magnetic.Magnetization

      

   .. py:attribute:: hubbard
      :type: aiida_atomistic.data.structure.hubbard.Hubbard

      

   .. py:method:: get_property_attribute(key)


   .. py:method:: set_property(pname=None, pvalue=None)


   .. py:method:: get_dimensionality()

      Return the dimensionality of the structure and its length/surface/volume.

      Zero-dimensional structures are assigned "volume" 0.

      :return: returns a dictionary with keys "dim" (dimensionality integer), "label" (dimensionality label)
          and "value" (numerical length/surface/volume).


   .. py:method:: set_ase(aseatoms)

      Load the structure from a ASE object


   .. py:method:: set_pymatgen(obj, **kwargs)

      Load the structure from a pymatgen object.

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).


   .. py:method:: set_pymatgen_molecule(mol, margin=5)

      Load the structure from a pymatgen Molecule object.

      :param margin: the margin to be added in all directions of the
          bounding box of the molecule.

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).


   .. py:method:: set_pymatgen_structure(struct)

      Load the structure from a pymatgen Structure object.

      .. note:: periodic boundary conditions are set to True in all
          three directions.
      .. note:: Requires the pymatgen module (version >= 3.3.5, usage
          of earlier versions may cause errors).

      :raise ValueError: if there are partial occupancies together with spins.


   .. py:method:: _validate()

      Performs some standard validation tests.


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


   .. py:method:: get_description()

      Returns a string with infos retrieved from StructureData node's properties

      :param self: the StructureData node
      :return: retsrt: the description string


   .. py:method:: get_symbols_set()

      Return a set containing the names of all elements involved in
      this structure (i.e., for it joins the list of symbols for each
      kind k in the structure).

      :returns: a set of strings of element names.


   .. py:method:: get_formula(mode='hill', separator='')

      Return a string with the chemical formula.

      :param mode: a string to specify how to generate the formula, can
          assume one of the following values:

          * 'hill' (default): count the number of atoms of each species,
            then use Hill notation, i.e. alphabetical order with C and H
            first if one or several C atom(s) is (are) present, e.g.
            ``['C','H','H','H','O','C','H','H','H']`` will return ``'C2H6O'``
            ``['S','O','O','H','O','H','O']``  will return ``'H2O4S'``
            From E. A. Hill, J. Am. Chem. Soc., 22 (8), pp 478–494 (1900)

          * 'hill_compact': same as hill but the number of atoms for each
            species is divided by the greatest common divisor of all of them, e.g.
            ``['C','H','H','H','O','C','H','H','H','O','O','O']``
            will return ``'CH3O2'``

          * 'reduce': group repeated symbols e.g.
            ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
            'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'BaTiO3BaTiO3BaTi2O3'``

          * 'group': will try to group as much as possible parts of the formula
            e.g.
            ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
            'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'(BaTiO3)2BaTi2O3'``

          * 'count': same as hill (i.e. one just counts the number
            of atoms of each species) without the re-ordering (take the
            order of the atomic sites), e.g.
            ``['Ba', 'Ti', 'O', 'O', 'O','Ba', 'Ti', 'O', 'O', 'O']``
            will return ``'Ba2Ti2O6'``

          * 'count_compact': same as count but the number of atoms
            for each species is divided by the greatest common divisor of
            all of them, e.g.
            ``['Ba', 'Ti', 'O', 'O', 'O','Ba', 'Ti', 'O', 'O', 'O']``
            will return ``'BaTiO3'``

      :param separator: a string used to concatenate symbols. Default empty.

      :return: a string with the formula

      .. note:: in modes reduce, group, count and count_compact, the
          initial order in which the atoms were appended by the user is
          used to group and/or order the symbols in the formula


   .. py:method:: get_site_kindnames()

      Return a list with length equal to the number of sites of this structure,
      where each element of the list is the kind name of the corresponding site.

      .. note:: This is NOT necessarily a list of chemical symbols! Use
          ``[ self.get_kind(s.kind_name).get_symbols_string() for s in self.sites]``
          for chemical symbols

      :return: a list of strings


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


   .. py:method:: get_ase()

      Get the ASE object.
      Requires to be able to import ase.

      :return: an ASE object corresponding to this
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        object.

      .. note:: If any site is an alloy or has vacancies, a ValueError
          is raised (from the site.get_ase() routine).


   .. py:method:: get_pymatgen(**kwargs)

      Get pymatgen object. Returns Structure for structures with
      periodic boundary conditions (in three dimensions) and Molecule
      otherwise.
      :param add_spin: True to add the spins to the pymatgen structure.
      Default is False (no spin added).

      .. note:: The spins are set according to the following rule:

          * if the kind name ends with 1 -> spin=+1

          * if the kind name ends with 2 -> spin=-1

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).


   .. py:method:: get_pymatgen_structure(**kwargs)

      Get the pymatgen Structure object.
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
      :raise ValueError: if periodic boundary conditions do not hold
        in at least one dimension of real space.


   .. py:method:: get_pymatgen_molecule()

      Get the pymatgen Molecule object.

      .. note:: Requires the pymatgen module (version >= 3.0.13, usage
          of earlier versions may cause errors).

      :return: a pymatgen Molecule object corresponding to this
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        object.


   .. py:method:: append_kind(kind)

      Append a kind to the
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`.
      It makes a copy of the kind.

      :param kind: the site to append, must be a Kind object.


   .. py:method:: append_site(site)

      Append a site to the
      :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`.
      It makes a copy of the site.

      :param site: the site to append. It must be a Site object.


   .. py:method:: append_atom(**kwargs)

      Append an atom to the Structure, taking care of creating the
      corresponding kind.

      :param ase: the ase Atom object from which we want to create a new atom
              (if present, this must be the only parameter)
      :param position: the position of the atom (three numbers in angstrom)
      :param symbols: passed to the constructor of the Kind object.
      :param weights: passed to the constructor of the Kind object.
      :param name: passed to the constructor of the Kind object. See also the note below.

      .. note :: Note on the 'name' parameter (that is, the name of the kind):

          * if specified, no checks are done on existing species. Simply,
            a new kind with that name is created. If there is a name
            clash, a check is done: if the kinds are identical, no error
            is issued; otherwise, an error is issued because you are trying
            to store two different kinds with the same name.

          * if not specified, the name is automatically generated. Before
            adding the kind, a check is done. If other species with the
            same properties already exist, no new kinds are created, but
            the site is added to the existing (identical) kind.
            (Actually, the first kind that is encountered).
            Otherwise, the name is made unique first, by adding to the string
            containing the list of chemical symbols a number starting from 1,
            until an unique name is found

      .. note :: checks of equality of species are done using
        the :py:meth:`~aiida.orm.nodes.data.structure.Kind.compare_with` method.


   .. py:method:: clear_kinds()

      Removes all kinds for the StructureData object.

      .. note:: Also clear all sites!


   .. py:method:: clear_sites()

      Removes all sites for the StructureData object.


   .. py:method:: get_kind(kind_name)

      Return the kind object associated with the given kind name.

      :param kind_name: String, the name of the kind you want to get

      :return: The Kind object associated with the given kind_name, if
         a Kind with the given name is present in the structure.

      :raise: ValueError if the kind_name is not present.


   .. py:method:: get_kind_names()

      Return a list of kind names (in the same order of the ``self.kinds``
      property, but return the names rather than Kind objects)

      .. note:: This is NOT necessarily a list of chemical symbols! Use
          get_symbols_set for chemical symbols

      :return: a list of strings.


   .. py:method:: set_cell(value)

      Set the cell.


   .. py:method:: reset_cell(new_cell)

      Reset the cell of a structure not yet stored to a new value.

      :param new_cell: list specifying the cell vectors

      :raises:
          ModificationNotAllowed: if object is already stored


   .. py:method:: reset_sites_positions(new_positions, conserve_particle=True)

      Replace all the Site positions attached to the Structure

      :param new_positions: list of (3D) positions for every sites.

      :param conserve_particle: if True, allows the possibility of removing a site.
          currently not implemented.

      :raises aiida.common.ModificationNotAllowed: if object is stored already
      :raises ValueError: if positions are invalid

      .. note:: it is assumed that the order of the new_positions is
          given in the same order of the one it's substituting, i.e. the
          kind of the site will not be checked.


   .. py:method:: set_pbc(value)

      Set the periodic boundary conditions.


   .. py:method:: set_cell_lengths(value)
      :abstractmethod:


   .. py:method:: set_cell_angles(value)
      :abstractmethod:


   .. py:method:: get_cell_volume()

      Returns the three-dimensional cell volume in Angstrom^3.

      Use the `get_dimensionality` method in order to get the area/length of lower-dimensional cells.

      :return: a float.


   .. py:method:: get_cif(converter='ase', store=False, **kwargs)

      Creates :py:class:`aiida.orm.nodes.data.cif.CifData`.

      .. versionadded:: 1.0
         Renamed from _get_cif

      :param converter: specify the converter. Default 'ase'.
      :param store: If True, intermediate calculation gets stored in the
          AiiDA database for record. Default False.
      :return: :py:class:`aiida.orm.nodes.data.cif.CifData` node.


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
      :raise ValueError: if periodic boundary conditions does not hold
        in at least one dimension of real space; if there are partial occupancies
        together with spins (defined by kind names ending with '1' or '2').

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



.. py:class:: Kind(**kwargs)


   This class contains the information about the species (kinds) of the system.

   It can be a single atom, or an alloy, or even contain vacancies.

   .. py:property:: name

      Return the name of this kind.
      The name of a kind is used to identify the species of a site.

      :return: a string


   .. py:property:: mass

      The mass of this species kind.

      :return: a float


   .. py:property:: weights

      Weights for this species kind. Refer also to
      :func:validate_symbols_tuple for the validation rules on the weights.


   .. py:property:: symbol

      If the kind has only one symbol, return it; otherwise, raise a
      ValueError.


   .. py:property:: symbols

      List of symbols for this site. If the site is a single atom,
      pass a list of one element only, or simply the string for that atom.
      For alloys, a list of elements.

      .. note:: Note that if you change the list of symbols, the kind
          name remains unchanged.


   .. py:property:: is_alloy

      Return whether the Kind is an alloy, i.e. contains more than one element

      :return: boolean, True if the kind has more than one element, False otherwise.


   .. py:property:: has_vacancies

      Return whether the Kind contains vacancies, i.e. when the sum of the weights is less than one.

      .. note:: the property uses the internal variable `_SUM_THRESHOLD` as a threshold.

      :return: boolean, True if the sum of the weights is less than one, False otherwise


   .. py:method:: get_raw()

      Return the raw version of the site, mapped to a suitable dictionary.
      This is the format that is actually used to store each kind of the
      structure in the DB.

      :return: a python dictionary with the kind.


   .. py:method:: reset_mass()

      Reset the mass to the automatic calculated value.

      The mass can be set manually; by default, if not provided,
      it is the mass of the constituent atoms, weighted with their
      weight (after the weight has been normalized to one to take
      correctly into account vacancies).

      This function uses the internal _symbols and _weights values and
      thus assumes that the values are validated.

      It sets the mass to None if the sum of weights is zero.


   .. py:method:: set_automatic_kind_name(tag=None)

      Set the type to a string obtained with the symbols appended one
      after the other, without spaces, in alphabetical order;
      if the site has a vacancy, a X is appended at the end too.


   .. py:method:: compare_with(other_kind)

      Compare with another Kind object to check if they are different.

      .. note:: This does NOT check the 'type' attribute. Instead, it compares
          (with reasonable thresholds, where applicable): the mass, and the list
          of symbols and of weights. Moreover, it compares the
          ``_internal_tag``, if defined (at the moment, defined automatically
          only when importing the Kind from ASE, if the atom has a non-zero tag).
          Note that the _internal_tag is only used while the class is loaded,
          but is not persisted on the database.

      :return: A tuple with two elements. The first one is True if the two sites
          are 'equivalent' (same mass, symbols and weights), False otherwise.
          The second element of the tuple is a string,
          which is either None (if the first element was True), or contains
          a 'human-readable' description of the first difference encountered
          between the two sites.


   .. py:method:: get_symbols_string()

      Return a string that tries to match as good as possible the symbols
      of this kind. If there is only one symbol (no alloy) with 100%
      occupancy, just returns the symbol name. Otherwise, groups the full
      string in curly brackets, and try to write also the composition
      (with 2 precision only).

      .. note:: If there is a vacancy (sum of weights<1), we indicate it
          with the X symbol followed by 1-sum(weights) (still with 2
          digits precision, so it can be 0.00)

      .. note:: Note the difference with respect to the symbols and the
          symbol properties!


   .. py:method:: set_symbols_and_weights(symbols, weights)

      Set the chemical symbols and the weights for the site.

      .. note:: Note that the kind name remains unchanged.


   .. py:method:: __repr__()

      Return repr(self).


   .. py:method:: __str__()

      Return str(self).



.. py:class:: Site(**kwargs)


   This class contains the information about a given site of the system.

   It can be a single atom, or an alloy, or even contain vacancies.

   .. py:property:: kind_name

      Return the kind name of this site (a string).

      The type of a site is used to decide whether two sites are identical
      (same mass, symbols, weights, ...) or not.


   .. py:property:: position

      Return the position of this site in absolute coordinates,
      in angstrom.


   .. py:method:: get_raw()

      Return the raw version of the site, mapped to a suitable dictionary.
      This is the format that is actually used to store each site of the
      structure in the DB.

      :return: a python dictionary with the site.


   .. py:method:: get_ase(kinds)

      Return a ase.Atom object for this site.

      :param kinds: the list of kinds from the StructureData object.

      .. note:: If any site is an alloy or has vacancies, a ValueError
          is raised (from the site.get_ase() routine).


   .. py:method:: __repr__()

      Return repr(self).


   .. py:method:: __str__()

      Return str(self).



