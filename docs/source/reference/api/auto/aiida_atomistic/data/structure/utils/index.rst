:py:mod:`aiida_atomistic.data.structure.utils`
==============================================

.. py:module:: aiida_atomistic.data.structure.utils


Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.utils.ObservedArray



Functions
~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.utils.efficient_copy
   aiida_atomistic.data.structure.utils._get_valid_cell
   aiida_atomistic.data.structure.utils._get_valid_pbc
   aiida_atomistic.data.structure.utils._check_valid_sites
   aiida_atomistic.data.structure.utils.has_ase
   aiida_atomistic.data.structure.utils.has_pymatgen
   aiida_atomistic.data.structure.utils.get_pymatgen_version
   aiida_atomistic.data.structure.utils.has_spglib
   aiida_atomistic.data.structure.utils.get_dimensionality
   aiida_atomistic.data.structure.utils.calc_cell_volume
   aiida_atomistic.data.structure.utils._create_symbols_tuple
   aiida_atomistic.data.structure.utils._create_weights_tuple
   aiida_atomistic.data.structure.utils.create_automatic_kind_name
   aiida_atomistic.data.structure.utils.validate_weights_tuple
   aiida_atomistic.data.structure.utils.is_valid_symbol
   aiida_atomistic.data.structure.utils.validate_symbols_tuple
   aiida_atomistic.data.structure.utils.group_symbols
   aiida_atomistic.data.structure.utils.get_formula_from_symbol_list
   aiida_atomistic.data.structure.utils.get_formula_group
   aiida_atomistic.data.structure.utils.get_formula
   aiida_atomistic.data.structure.utils.get_symbols_string
   aiida_atomistic.data.structure.utils.has_vacancies
   aiida_atomistic.data.structure.utils.symop_ortho_from_fract
   aiida_atomistic.data.structure.utils.symop_fract_from_ortho
   aiida_atomistic.data.structure.utils.ase_refine_cell
   aiida_atomistic.data.structure.utils.atom_kinds_to_html
   aiida_atomistic.data.structure.utils.create_automatic_kind_name
   aiida_atomistic.data.structure.utils.set_symbols_and_weights
   aiida_atomistic.data.structure.utils.check_is_alloy
   aiida_atomistic.data.structure.utils.check_plugin_support
   aiida_atomistic.data.structure.utils.order_k
   aiida_atomistic.data.structure.utils.compress_properties_by_kind
   aiida_atomistic.data.structure.utils.rebuild_site_lists_from_kind_lists
   aiida_atomistic.data.structure.utils.build_sites_from_expanded_properties
   aiida_atomistic.data.structure.utils.classify_site_kinds
   aiida_atomistic.data.structure.utils.check_kinds_match
   aiida_atomistic.data.structure.utils.sites_from_kinds



Attributes
~~~~~~~~~~

.. autoapisummary::

   aiida_atomistic.data.structure.utils._MASS_THRESHOLD
   aiida_atomistic.data.structure.utils._SUM_THRESHOLD
   aiida_atomistic.data.structure.utils._DEFAULT_CELL
   aiida_atomistic.data.structure.utils._valid_symbols
   aiida_atomistic.data.structure.utils._atomic_masses
   aiida_atomistic.data.structure.utils._atomic_numbers
   aiida_atomistic.data.structure.utils._dimensionality_label


.. py:data:: _MASS_THRESHOLD
   :value: 0.001



.. py:data:: _SUM_THRESHOLD
   :value: 1e-06



.. py:data:: _DEFAULT_CELL
   :value: ((0, 0, 0), (0, 0, 0), (0, 0, 0))



.. py:data:: _valid_symbols



.. py:data:: _atomic_masses



.. py:data:: _atomic_numbers



.. py:data:: _dimensionality_label



.. py:class:: ObservedArray(shape, dtype=float, buffer=None, offset=0, strides=None, order=None)


   Bases: :py:obj:`numpy.ndarray`

   This is a subclass of numpy.ndarray that allows to observe changes to the array.
   In this way, full flexibility of StructureDataMutable is achieved and at the same
   time we can keep track of all the changes.

   .. py:method:: __setitem__(index, value)

      Set the value of an item in the ObservedArray.

      Parameters:
      - index: int or tuple
          The index or indices of the item(s) to be set.
      - value: any
          The value to be assigned to the item(s).

      Returns:
      None


   .. py:method:: __array_finalize__(obj)

      Finalize the creation of the ObservedArray.

      This method is called when the view is created or sliced.

      Parameters:
      - obj: ObservedArray or None
          The object being finalized.

      Returns:
      None



.. py:function:: efficient_copy(self)


.. py:function:: _get_valid_cell(inputcell)

   Return the cell in a valid format from a generic input.

   :raise ValueError: whenever the format is not valid.


.. py:function:: _get_valid_pbc(inputpbc)

   Return a list of three booleans for the periodic boundary conditions,
   in a valid format from a generic input.

   :raise ValueError: if the format is not valid.


.. py:function:: _check_valid_sites(sites)

   Check that no two sites have positions that are too close to each other.


.. py:function:: has_ase()

   :return: True if the ase module can be imported, False otherwise.


.. py:function:: has_pymatgen()

   :return: True if the pymatgen module can be imported, False otherwise.


.. py:function:: get_pymatgen_version()

   :return: string with pymatgen version, None if can not import.


.. py:function:: has_spglib()

   :return: True if the spglib module can be imported, False otherwise.


.. py:function:: get_dimensionality(pbc, cell)

   Return the dimensionality of the structure and its length/surface/volume.

   Zero-dimensional structures are assigned "volume" 0.

   :return: returns a dictionary with keys "dim" (dimensionality integer), "label" (dimensionality label)
       and "value" (numerical length/surface/volume).


.. py:function:: calc_cell_volume(cell)

   Compute the three-dimensional cell volume in Angstrom^3.

   :param cell: the cell vectors; the must be a 3x3 list of lists of floats
   :returns: the cell volume.


.. py:function:: _create_symbols_tuple(symbols)

   Returns a tuple with the symbols provided. If a string is provided,
   this is converted to a tuple with one single element.


.. py:function:: _create_weights_tuple(weights)

   Returns a tuple with the weights provided. If a number is provided,
   this is converted to a tuple with one single element.
   If None is provided, this is converted to the tuple (1.,)


.. py:function:: create_automatic_kind_name(symbols, weights)

   Create a string obtained with the symbols appended one
   after the other, without spaces, in alphabetical order;
   if the site has a vacancy, a X is appended at the end too.


.. py:function:: validate_weights_tuple(weights_tuple, threshold)

   Validates the weight of the atomic kinds.

   :raise: ValueError if the weights_tuple is not valid.

   :param weights_tuple: the tuple to validate. It must be a
           a tuple of floats (as created by :func:_create_weights_tuple).
   :param threshold: a float number used as a threshold to check that the sum
           of the weights is <= 1.

   If the sum is less than one, it means that there are vacancies.
   Each element of the list must be >= 0, and the sum must be <= 1.


.. py:function:: is_valid_symbol(symbol)

   Validates the chemical symbol name.

   :return: True if the symbol is a valid chemical symbol (with correct
       capitalization), or the dummy X, False otherwise.

   Recognized symbols are for elements from hydrogen (Z=1) to lawrencium
   (Z=103). In addition, a dummy element unknown name (Z=0) is supported.


.. py:function:: validate_symbols_tuple(symbols_tuple)

   Used to validate whether the chemical species are valid.

   :param symbols_tuple: a tuple (or list) with the chemical symbols name.
   :raises: UnsupportedSpeciesError if any symbol in the tuple is not a valid chemical
       symbol (with correct capitalization).

   Refer also to the documentation of :func:is_valid_symbol


.. py:function:: group_symbols(_list)

   Group a list of symbols to a list containing the number of consecutive
   identical symbols, and the symbol itself.

   Examples
   --------
   * ``['Ba','Ti','O','O','O','Ba']`` will return
     ``[[1,'Ba'],[1,'Ti'],[3,'O'],[1,'Ba']]``

   * ``[ [ [1,'Ba'],[1,'Ti'] ],[ [1,'Ba'],[1,'Ti'] ] ]`` will return
     ``[[2, [ [1, 'Ba'], [1, 'Ti'] ] ]]``

   :param _list: a list of elements representing a chemical formula
   :return: a list of length-2 lists of the form [ multiplicity , element ]


.. py:function:: get_formula_from_symbol_list(_list, separator='')

   Return a string with the formula obtained from the list of symbols.

   Examples
   --------
   * ``[[1,'Ba'],[1,'Ti'],[3,'O']]`` will return ``'BaTiO3'``
   * ``[[2, [ [1, 'Ba'], [1, 'Ti'] ] ]]`` will return ``'(BaTi)2'``

   :param _list: a list of symbols and multiplicities as obtained from
       the function group_symbols
   :param separator: a string used to concatenate symbols. Default empty.

   :return: a string


.. py:function:: get_formula_group(symbol_list, separator='')

   Return a string with the chemical formula from a list of chemical symbols.
   The formula is written in a compact" way, i.e. trying to group as much as
   possible parts of the formula.

   .. note:: it works for instance very well if structure was obtained
       from an ASE supercell.

   Example of result:
   ``['Ba', 'Ti', 'O', 'O', 'O', 'Ba', 'Ti', 'O', 'O', 'O',
   'Ba', 'Ti', 'Ti', 'O', 'O', 'O']`` will return ``'(BaTiO3)2BaTi2O3'``.

   :param symbol_list: list of symbols
       (e.g. ['Ba','Ti','O','O','O'])
   :param separator: a string used to concatenate symbols. Default empty.
   :returns: a string with the chemical formula for the given structure.


.. py:function:: get_formula(sites, mode='hill', separator='')

   Return a string with the chemical formula.

   :param symbol_list: a list of symbols, e.g. ``['H','H','O']``
   :param mode: a string to specify how to generate the formula, can
       assume one of the following values:

       * 'hill' (default): count the number of atoms of each species,
         then use Hill notation, i.e. alphabetical order with C and H
         first if one or several C atom(s) is (are) present, e.g.
         ``['C','H','H','H','O','C','H','H','H']`` will return ``'C2H6O'``
         ``['S','O','O','H','O','H','O']``  will return ``'H2O4S'``
         From E. A. Hill, J. Am. Chem. Soc., 22 (8), pp 478-494 (1900)

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


.. py:function:: get_symbols_string(symbols, weights)

   Return a string that tries to match as good as possible the symbols
   and weights. If there is only one symbol (no alloy) with 100%
   occupancy, just returns the symbol name. Otherwise, groups the full
   string in curly brackets, and try to write also the composition
   (with 2 precision only).
   If (sum of weights<1), we indicate it with the X symbol followed
   by 1-sum(weights) (still with 2 digits precision, so it can be 0.00)

   :param symbols: the symbols as obtained from <kind>._symbols
   :param weights: the weights as obtained from <kind>._weights

   .. note:: Note the difference with respect to the symbols and the
       symbol properties!


.. py:function:: has_vacancies(weights)

   Returns True if the sum of the weights is less than one.
   It uses the internal variable _SUM_THRESHOLD as a threshold.
   :param weights: the weights
   :return: a boolean


.. py:function:: symop_ortho_from_fract(cell)

   Creates a matrix for conversion from orthogonal to fractional
   coordinates.

   Taken from
   svn://www.crystallography.net/cod-tools/trunk/lib/perl5/Fractional.pm,
   revision 850.

   :param cell: array of cell parameters (three lengths and three angles)


.. py:function:: symop_fract_from_ortho(cell)

   Creates a matrix for conversion from fractional to orthogonal
   coordinates.

   Taken from
   svn://www.crystallography.net/cod-tools/trunk/lib/perl5/Fractional.pm,
   revision 850.

   :param cell: array of cell parameters (three lengths and three angles)


.. py:function:: ase_refine_cell(aseatoms, **kwargs)

   Detect the symmetry of the structure, remove symmetric atoms and
   refine unit cell.

   :param aseatoms: an ase.atoms.Atoms instance
   :param symprec: symmetry precision, used by spglib
   :return newase: refined cell with reduced set of atoms
   :return symmetry: a dictionary describing the symmetry space group


.. py:function:: atom_kinds_to_html(atom_kind)

   Construct in html format

   an alloy with 0.5 Ge, 0.4 Si and 0.1 vacancy is represented as
   Ge<sub>0.5</sub> + Si<sub>0.4</sub> + vacancy<sub>0.1</sub>

   Args:
   -----
       atom_kind: a string with the name of the atomic kind, as printed by
       kind.get_symbols_string(), e.g. Ba0.80Ca0.10X0.10

   Returns:
   --------
       html code for rendered formula


.. py:function:: create_automatic_kind_name(symbols, weights)

   Create a string obtained with the symbols appended one
   after the other, without spaces, in alphabetical order;
   if the site has a vacancy, a X is appended at the end too.


.. py:function:: set_symbols_and_weights(new_data)

   Set the chemical symbols and the weights for the site.

   .. note:: Note that the kind name remains unchanged.


.. py:function:: check_is_alloy(data)

   Check if the data is an alloy or not.

   :param data: the data to check. The dict of the SiteCore model.
   :return: True if the data is an alloy, False otherwise.


.. py:function:: check_plugin_support(structure, plugin_properties: set) -> set

   Check if the plugin supports the given properties.
   :param plugin_properties: The supported properties in the plugin.
   :return: the defined properties which are not supported by the plugin
   :rtype: set


.. py:function:: order_k(k)

   Adjusts the order of elements in the array `k` by ensuring that there are no gaps in the sequence.

   If the minimum value in `k` is 0, it increments all elements by 1. Then, it iterates from the maximum value
   in `k` down to the minimum value, checking if each value minus one is not in `k`. If a value minus one is not
   found, it decrements all elements in `k` that are greater than or equal to the current value.

   Parameters:
   k (numpy.ndarray): An array of integers to be reordered.

   Returns:
   numpy.ndarray: The reordered array `k`.


.. py:function:: compress_properties_by_kind(props)

   Compress site-wise properties into kind-wise lists.
   Returns a dict with properties as lists, one entry per kind.


.. py:function:: rebuild_site_lists_from_kind_lists(compressed)

   Expand kinds into a list of site dictionaries, sorted by site_index.


.. py:function:: build_sites_from_expanded_properties(expanded)

   Build the structure dictionary from expanded site-wise lists of properties.


.. py:function:: classify_site_kinds(sites: list, exclude_props: bool = None, tolerance: Union[dict, float] = 0.001)

   Classify sites into groups where each group (kind) has the same properties except position.

   Args:
       sites: List of site dictionaries
       exclude_props: Set of property names to exclude from grouping (default: {'position'})
       tolerance: Numerical tolerance for floating point comparisons (default: 1e-3)

   Returns:
       dict: {group_key: {'sites': [site_indices], 'properties': {prop: value}}}


.. py:function:: check_kinds_match(structure, kinds_list)


.. py:function:: sites_from_kinds(kinds)

   Expand kinds into a list of site dictionaries, sorted by site_index.
   1. Create a list of site indices and positions from the kinds
   2. Create a list of site dictionaries by copying the kind properties
      and adding the position
   3. Return the list of site dictionaries
   4. Note: the returned list is sorted by site_index

   Format of kinds (basically what can be obtained by structure.generate_kinds()):
   [
       {'site_indices': [0, 2],
       'positions': [array([0., 0., 0.]), array([0., 1., 0.])],
       'symbol': 'H',
       'mass': 1.008,
       'charge': 0.0,
       'magmom': (0.0, 0.0, -1.0),
       'kind_name': 'H1'},
       {'site_indices': [1],
       'positions': [array([0., 0., 1.])],
       'symbol': 'O',
       'mass': 15.999,
       'charge': -2.0,
       'magmom': (0.0, 0.0, 1.0),
       'kind_name': 'O1'}
   ]
