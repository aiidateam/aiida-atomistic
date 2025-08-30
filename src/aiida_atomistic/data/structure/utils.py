import copy
import functools
import re

import numpy as np

from aiida.common.constants import elements
from aiida.common.exceptions import UnsupportedSpeciesError

try:
    import ase  # noqa: F401
except ImportError:
    pass

try:
    import pymatgen.core as core  # noqa: F401
except ImportError:
    pass


from aiida.engine import calcfunction
from aiida.orm import List

from .structure import StructureData

# Threshold used to check if the mass of two different Site objects is the same.

_MASS_THRESHOLD = 1.0e-3
# Threshold to check if the sum is one or not
_SUM_THRESHOLD = 1.0e-6
# Default cell
_DEFAULT_CELL = ((0, 0, 0), (0, 0, 0), (0, 0, 0))

_valid_symbols = tuple(i["symbol"] for i in elements.values())
_atomic_masses = {el["symbol"]: el["mass"] for el in elements.values()}
_atomic_numbers = {data["symbol"]: num for num, data in elements.items()}
_dimensionality_label = {0: '', 1: 'length', 2: 'surface', 3: 'volume'}

class ObservedArray(np.ndarray):
    """
    This is a subclass of numpy.ndarray that allows to observe changes to the array.
    In this way, full flexibility of StructureDataMutable is achieved and at the same
    time we can keep track of all the changes.
    """

    def __new__(cls, input_array):
        """
        Create a new instance of ObservedArray.

        Parameters:
        - input_array: array-like
            The input array to be converted to an instance of ObservedArray.

        Returns:
        - obj: ObservedArray
            The new instance of ObservedArray.
        """
        obj = np.asarray(input_array).view(cls)
        return obj

    def __setitem__(self, index, value):
        """
        Set the value of an item in the ObservedArray.

        Parameters:
        - index: int or tuple
            The index or indices of the item(s) to be set.
        - value: any
            The value to be assigned to the item(s).

        Returns:
        None
        """
        super(ObservedArray, self).__setitem__(index, value)

    def __array_finalize__(self, obj):
        """
        Finalize the creation of the ObservedArray.

        This method is called when the view is created or sliced.

        Parameters:
        - obj: ObservedArray or None
            The object being finalized.

        Returns:
        None
        """
        if obj is None:
            return

def _get_valid_cell(inputcell):
    """Return the cell in a valid format from a generic input.

    :raise ValueError: whenever the format is not valid.
    """
    try:
        the_cell = list(list(float(c) for c in i) for i in inputcell)
        if len(the_cell) != 3:
            raise ValueError
        if any(len(i) != 3 for i in the_cell):
            raise ValueError
    except (IndexError, ValueError, TypeError):
        raise ValueError(
            "Cell must be a list of three vectors, each defined as a list of three coordinates."
        )

    return np.array(the_cell)


def _get_valid_pbc(inputpbc):
    """Return a list of three booleans for the periodic boundary conditions,
    in a valid format from a generic input.

    :raise ValueError: if the format is not valid.
    """
    if isinstance(inputpbc, bool):
        the_pbc = [inputpbc, inputpbc, inputpbc]
    elif hasattr(inputpbc, "__iter__"):
        # To manage numpy lists of bools, whose elements are of type numpy.bool_
        # and for which isinstance(i,bool) return False...
        if hasattr(inputpbc, "tolist"):
            the_value = list(i for i in inputpbc.tolist())
        else:
            the_value = inputpbc
        if all(isinstance(i, bool) for i in the_value):
            if len(the_value) == 3:
                the_pbc = list(i for i in the_value)
            elif len(the_value) == 1:
                the_pbc = (the_value[0], the_value[0], the_value[0])
            else:
                raise ValueError("pbc length must be either one or three.")
        else:
            raise ValueError("pbc elements are not booleans.")
    else:
        raise ValueError("pbc must be a boolean or a list of three booleans.", inputpbc)

    return the_pbc

def _check_valid_sites(sites):

    num_sites = len(sites)

    for i in range(num_sites):
        for j in range(num_sites):
            if j == i:
                continue
            if np.allclose(sites[i]["position"], sites[j]["position"], atol=1e-3):
                raise ValueError(f"Sites {i+1} and {j+1} cannot have the same position!")

    return


def has_ase():
    """:return: True if the ase module can be imported, False otherwise."""
    try:
        import ase  # noqa: F401
    except ImportError:
        return False
    return True


def has_pymatgen():
    """:return: True if the pymatgen module can be imported, False otherwise."""
    try:
        import pymatgen  # noqa: F401
    except ImportError:
        return False
    return True


def get_pymatgen_version():
    """:return: string with pymatgen version, None if can not import."""
    if not has_pymatgen():
        return None
    try:
        from pymatgen import __version__
    except ImportError:
        # this was changed in version 2022.0.3
        from pymatgen.core import __version__
    return __version__


def has_spglib():
    """:return: True if the spglib module can be imported, False otherwise."""
    try:
        import spglib  # noqa: F401
    except ImportError:
        return False
    return True

def get_dimensionality(
    pbc,
    cell,
):
    """Return the dimensionality of the structure and its length/surface/volume.

    Zero-dimensional structures are assigned "volume" 0.

    :return: returns a dictionary with keys "dim" (dimensionality integer), "label" (dimensionality label)
        and "value" (numerical length/surface/volume).
    """
    import numpy as np

    retdict = {}

    pbc = np.array(pbc)
    cell = np.array(cell)

    dim = len(pbc[pbc])

    retdict["dim"] = dim
    retdict["label"] = _dimensionality_label[dim]

    if dim not in (0, 1, 2, 3):
        raise ValueError(f"Dimensionality {dim} must be one of 0, 1, 2, 3")

    if dim == 0:
        # We have no concept of 0d volume. Let's return a value of 0 for a consistent output dictionary
        retdict["value"] = 0
    elif dim == 1:
        retdict["value"] = np.linalg.norm(cell[pbc])
    elif dim == 2:
        vectors = cell[pbc]
        retdict["value"] = np.linalg.norm(np.cross(vectors[0], vectors[1]))
    elif dim == 3:
        retdict["value"] = calc_cell_volume(cell)

    return retdict

def calc_cell_volume(cell):
    """Compute the three-dimensional cell volume in Angstrom^3.

    :param cell: the cell vectors; the must be a 3x3 list of lists of floats
    :returns: the cell volume.
    """
    return np.abs(np.dot(cell[0], np.cross(cell[1], cell[2])))


def _create_symbols_tuple(symbols):
    """Returns a tuple with the symbols provided. If a string is provided,
    this is converted to a tuple with one single element.
    """
    if isinstance(symbols, str):
        symbols_list = re.sub( r"([A-Z])", r" \1", symbols).split()
    else:
        symbols_list = tuple(symbols)

    for symbol in symbols_list:
        if symbol not in _valid_symbols:
            raise ValueError(f"Some or all of the symbols provided are not correct: {symbols_list}")
    return symbols_list


def _create_weights_tuple(weights):
    """Returns a tuple with the weights provided. If a number is provided,
    this is converted to a tuple with one single element.
    If None is provided, this is converted to the tuple (1.,)
    """
    import numbers

    if weights is None:
        weights_tuple = (1.0,)
    elif isinstance(weights, numbers.Number):
        weights_tuple = (weights,)
    else:
        weights_tuple = tuple(float(i) for i in weights)
    return weights_tuple


def create_automatic_kind_name(symbols, weights):
    """Create a string obtained with the symbols appended one
    after the other, without spaces, in alphabetical order;
    if the site has a vacancy, a X is appended at the end too.
    """
    sorted_symbol_list = list(set(symbols))
    sorted_symbol_list.sort()  # In-place sort
    name_string = "".join(sorted_symbol_list)
    if has_vacancies(weights):
        name_string += "X"
    return name_string


def validate_weights_tuple(weights_tuple, threshold):
    """Validates the weight of the atomic kinds.

    :raise: ValueError if the weights_tuple is not valid.

    :param weights_tuple: the tuple to validate. It must be a
            a tuple of floats (as created by :func:_create_weights_tuple).
    :param threshold: a float number used as a threshold to check that the sum
            of the weights is <= 1.

    If the sum is less than one, it means that there are vacancies.
    Each element of the list must be >= 0, and the sum must be <= 1.
    """
    w_sum = sum(weights_tuple)
    if any(i < 0.0 for i in weights_tuple) or (w_sum - 1.0 > threshold):
        raise ValueError(
            "The weight list is not valid (each element must be positive, and the sum must be <= 1)."
        )


def is_valid_symbol(symbol):
    """Validates the chemical symbol name.

    :return: True if the symbol is a valid chemical symbol (with correct
        capitalization), or the dummy X, False otherwise.

    Recognized symbols are for elements from hydrogen (Z=1) to lawrencium
    (Z=103). In addition, a dummy element unknown name (Z=0) is supported.
    """
    return symbol in _valid_symbols


def validate_symbols_tuple(symbols_tuple):
    """Used to validate whether the chemical species are valid.

    :param symbols_tuple: a tuple (or list) with the chemical symbols name.
    :raises: UnsupportedSpeciesError if any symbol in the tuple is not a valid chemical
        symbol (with correct capitalization).

    Refer also to the documentation of :func:is_valid_symbol
    """
    if len(symbols_tuple) == 0:
        valid = False
    else:
        valid = all(is_valid_symbol(sym) for sym in symbols_tuple)
    if not valid:
        raise UnsupportedSpeciesError(
            f"At least one element of the symbol list {symbols_tuple} has not been recognized."
        )


def group_symbols(_list):
    """Group a list of symbols to a list containing the number of consecutive
    identical symbols, and the symbol itself.

    Examples
    --------
    * ``['Ba','Ti','O','O','O','Ba']`` will return
      ``[[1,'Ba'],[1,'Ti'],[3,'O'],[1,'Ba']]``

    * ``[ [ [1,'Ba'],[1,'Ti'] ],[ [1,'Ba'],[1,'Ti'] ] ]`` will return
      ``[[2, [ [1, 'Ba'], [1, 'Ti'] ] ]]``

    :param _list: a list of elements representing a chemical formula
    :return: a list of length-2 lists of the form [ multiplicity , element ]
    """
    the_list = copy.deepcopy(_list)
    the_list.reverse()
    grouped_list = [[1, the_list.pop()]]
    while the_list:
        elem = the_list.pop()
        if elem == grouped_list[-1][1]:
            # same symbol is repeated
            grouped_list[-1][0] += 1
        else:
            grouped_list.append([1, elem])

    return grouped_list


def get_formula_from_symbol_list(_list, separator=""):
    """Return a string with the formula obtained from the list of symbols.

    Examples
    --------
    * ``[[1,'Ba'],[1,'Ti'],[3,'O']]`` will return ``'BaTiO3'``
    * ``[[2, [ [1, 'Ba'], [1, 'Ti'] ] ]]`` will return ``'(BaTi)2'``

    :param _list: a list of symbols and multiplicities as obtained from
        the function group_symbols
    :param separator: a string used to concatenate symbols. Default empty.

    :return: a string
    """
    list_str = []
    for elem in _list:
        if elem[0] == 1:
            multiplicity_str = ""
        else:
            multiplicity_str = str(elem[0])

        if isinstance(elem[1], str):
            list_str.append(f"{elem[1]}{multiplicity_str}")
        elif elem[0] > 1:
            list_str.append(
                f"({get_formula_from_symbol_list(elem[1], separator=separator)}){multiplicity_str}"
            )
        else:
            list_str.append(
                f"{get_formula_from_symbol_list(elem[1], separator=separator)}{multiplicity_str}"
            )

    return separator.join(list_str)


def get_formula_group(symbol_list, separator=""):
    """Return a string with the chemical formula from a list of chemical symbols.
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
    """

    def group_together(_list, group_size, offset):
        """:param _list: a list
        :param group_size: size of the groups
        :param offset: beginning grouping after offset elements
        :return : a list of lists made of groups of size group_size
            obtained by grouping list elements together
            The first elements (up to _list[offset-1]) are not grouped
        example:
            ``group_together(['O','Ba','Ti','Ba','Ti'],2,1) =
                ['O',['Ba','Ti'],['Ba','Ti']]``
        """
        the_list = copy.deepcopy(_list)
        the_list.reverse()
        grouped_list = []
        for _ in range(offset):
            grouped_list.append([the_list.pop()])

        while the_list:
            sub_list = []
            for _ in range(group_size):
                if the_list:
                    sub_list.append(the_list.pop())
            grouped_list.append(sub_list)

        return grouped_list

    def cleanout_symbol_list(_list):
        """:param _list: a list of groups of symbols and multiplicities
        :return : a list where all groups with multiplicity 1 have
            been reduced to minimum
        example: ``[[1,[[1,'Ba']]]]`` will return ``[[1,'Ba']]``
        """
        the_list = []
        for elem in _list:
            if elem[0] == 1 and isinstance(elem[1], list):
                the_list.extend(elem[1])
            else:
                the_list.append(elem)

        return the_list

    def group_together_symbols(_list, group_size):
        """Successive application of group_together, group_symbols and
        cleanout_symbol_list, in order to group a symbol list, scanning all
        possible offsets, for a given group size
        :param _list: the symbol list (see function group_symbols)
        :param group_size: the size of the groups
        :return the_symbol_list: the new grouped symbol list
        :return has_grouped: True if we grouped something
        """
        the_symbol_list = copy.deepcopy(_list)
        has_grouped = False
        offset = 0
        while not has_grouped and offset < group_size:
            grouped_list = group_together(the_symbol_list, group_size, offset)
            new_symbol_list = group_symbols(grouped_list)
            if len(new_symbol_list) < len(grouped_list):
                the_symbol_list = copy.deepcopy(new_symbol_list)
                the_symbol_list = cleanout_symbol_list(the_symbol_list)
                has_grouped = True
                # print get_formula_from_symbol_list(the_symbol_list)
            offset += 1

        return the_symbol_list, has_grouped

    def group_all_together_symbols(_list):
        """Successive application of the function group_together_symbols, to group
        a symbol list, scanning all possible offsets and group sizes
        :param _list: the symbol list (see function group_symbols)
        :return: the new grouped symbol list
        """
        has_finished = False
        group_size = 2
        the_symbol_list = copy.deepcopy(_list)

        while not has_finished and group_size <= len(_list) // 2:
            # try to group as much as possible by groups of size group_size
            the_symbol_list, has_grouped = group_together_symbols(
                the_symbol_list, group_size
            )
            has_finished = has_grouped
            group_size += 1
            # stop as soon as we managed to group something
            # or when the group_size is too big to get anything

        return the_symbol_list

    # initial grouping of the chemical symbols
    old_symbol_list = [-1]
    new_symbol_list = group_symbols(symbol_list)

    # successively apply the grouping procedure until the symbol list does not
    # change anymore
    while new_symbol_list != old_symbol_list:
        old_symbol_list = copy.deepcopy(new_symbol_list)
        new_symbol_list = group_all_together_symbols(old_symbol_list)

    return get_formula_from_symbol_list(new_symbol_list, separator=separator)


def get_formula(sites, mode="hill", separator=""):
    """Return a string with the chemical formula.

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
    """

    symbol_list = [site.symbol for site in sites]

    if mode == "group":
        return get_formula_group(symbol_list, separator=separator)

    # for hill and count cases, simply count the occurences of each
    # chemical symbol (with some re-ordering in hill)
    if mode in ["hill", "hill_compact"]:
        if "C" in symbol_list:
            ordered_symbol_set = sorted(
                set(symbol_list), key=lambda elem: {"C": "0", "H": "1"}.get(elem, elem)
            )
        else:
            ordered_symbol_set = sorted(set(symbol_list))
        the_symbol_list = [
            [symbol_list.count(elem), elem] for elem in ordered_symbol_set
        ]

    elif mode in ["count", "count_compact"]:
        ordered_symbol_indexes = sorted(
            [symbol_list.index(elem) for elem in set(symbol_list)]
        )
        ordered_symbol_set = [symbol_list[i] for i in ordered_symbol_indexes]
        the_symbol_list = [
            [symbol_list.count(elem), elem] for elem in ordered_symbol_set
        ]

    elif mode == "reduce":
        the_symbol_list = group_symbols(symbol_list)

    else:
        raise ValueError(
            "Mode should be hill, hill_compact, group, reduce, count or count_compact"
        )

    if mode in ["hill_compact", "count_compact"]:
        from math import gcd

        the_gcd = functools.reduce(gcd, [e[0] for e in the_symbol_list])
        the_symbol_list = [[e[0] // the_gcd, e[1]] for e in the_symbol_list]

    return get_formula_from_symbol_list(the_symbol_list, separator=separator)


def get_symbols_string(symbols, weights):
    """Return a string that tries to match as good as possible the symbols
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
    """
    if len(symbols) == 1 and weights[0] == 1.0:
        return symbols[0]

    pieces = []
    for symbol, weight in zip(symbols, weights):
        pieces.append(f"{symbol}{weight:4.2f}")
    if has_vacancies(weights):
        pieces.append(f"X{1.0 - sum(weights):4.2f}")
    return f"{{{''.join(sorted(pieces))}}}"


def has_vacancies(weights):
    """Returns True if the sum of the weights is less than one.
    It uses the internal variable _SUM_THRESHOLD as a threshold.
    :param weights: the weights
    :return: a boolean
    """
    w_sum = sum(weights)
    return not 1.0 - w_sum < _SUM_THRESHOLD


def symop_ortho_from_fract(cell):
    """Creates a matrix for conversion from orthogonal to fractional
    coordinates.

    Taken from
    svn://www.crystallography.net/cod-tools/trunk/lib/perl5/Fractional.pm,
    revision 850.

    :param cell: array of cell parameters (three lengths and three angles)
    """
    import math

    import numpy

    a, b, c, alpha, beta, gamma = cell
    alpha, beta, gamma = (math.pi * x / 180 for x in [alpha, beta, gamma])
    ca, cb, cg = (math.cos(x) for x in [alpha, beta, gamma])
    sg = math.sin(gamma)

    return numpy.array(
        [
            [a, b * cg, c * cb],
            [0, b * sg, c * (ca - cb * cg) / sg],
            [0, 0, c * math.sqrt(sg * sg - ca * ca - cb * cb + 2 * ca * cb * cg) / sg],
        ]
    )


def symop_fract_from_ortho(cell):
    """Creates a matrix for conversion from fractional to orthogonal
    coordinates.

    Taken from
    svn://www.crystallography.net/cod-tools/trunk/lib/perl5/Fractional.pm,
    revision 850.

    :param cell: array of cell parameters (three lengths and three angles)
    """
    import math

    import numpy

    a, b, c, alpha, beta, gamma = cell
    alpha, beta, gamma = (math.pi * x / 180 for x in [alpha, beta, gamma])
    ca, cb, cg = (math.cos(x) for x in [alpha, beta, gamma])
    sg = math.sin(gamma)
    ctg = cg / sg
    D = math.sqrt(sg * sg - cb * cb - ca * ca + 2 * ca * cb * cg)  # noqa: N806

    return numpy.array(
        [
            [1.0 / a, -(1.0 / a) * ctg, (ca * cg - cb) / (a * D)],
            [0, 1.0 / (b * sg), -(ca - cb * cg) / (b * D * sg)],
            [0, 0, sg / (c * D)],
        ]
    )


def ase_refine_cell(aseatoms, **kwargs):
    """Detect the symmetry of the structure, remove symmetric atoms and
    refine unit cell.

    :param aseatoms: an ase.atoms.Atoms instance
    :param symprec: symmetry precision, used by spglib
    :return newase: refined cell with reduced set of atoms
    :return symmetry: a dictionary describing the symmetry space group
    """
    from ase.atoms import Atoms
    from spglib import get_symmetry_dataset, refine_cell

    spglib_tuple = (
        aseatoms.get_cell(),
        aseatoms.get_scaled_positions(),
        aseatoms.get_atomic_numbers(),
    )
    cell, positions, numbers = refine_cell(spglib_tuple, **kwargs)

    refined_atoms = (
        cell,
        positions,
        numbers,
    )
    sym_dataset = get_symmetry_dataset(refined_atoms, **kwargs)

    unique_numbers = []
    unique_positions = []

    for i in set(sym_dataset["equivalent_atoms"]):
        unique_numbers.append(numbers[i])
        unique_positions.append(positions[i])

    unique_atoms = Atoms(
        unique_numbers, scaled_positions=unique_positions, cell=cell, pbc=True
    )

    return unique_atoms, {
        "hm": sym_dataset["international"],
        "hall": sym_dataset["hall"],
        "tables": sym_dataset["number"],
        "rotations": sym_dataset["rotations"],
        "translations": sym_dataset["translations"],
    }


def atom_kinds_to_html(atom_kind):
    """Construct in html format

    an alloy with 0.5 Ge, 0.4 Si and 0.1 vacancy is represented as
    Ge<sub>0.5</sub> + Si<sub>0.4</sub> + vacancy<sub>0.1</sub>

    Args:
    -----
        atom_kind: a string with the name of the atomic kind, as printed by
        kind.get_symbols_string(), e.g. Ba0.80Ca0.10X0.10

    Returns:
    --------
        html code for rendered formula
    """
    # Parse the formula (TODO can be made more robust though never fails if
    # it takes strings generated with kind.get_symbols_string())
    import re

    matched_elements = re.findall(r"([A-Z][a-z]*)([0-1][.[0-9]*]?)?", atom_kind)

    # Compose the html string
    html_formula_pieces = []

    for element in matched_elements:
        # replace element X by 'vacancy'
        species = element[0] if element[0] != "X" else "vacancy"
        weight = element[1] if element[1] != "" else None

        if weight is not None:
            html_formula_pieces.append(f"{species}<sub>{weight}</sub>")
        else:
            html_formula_pieces.append(species)

    html_formula = " + ".join(html_formula_pieces)

    return html_formula


def create_automatic_kind_name(symbols, weights):
    """Create a string obtained with the symbols appended one
    after the other, without spaces, in alphabetical order;
    if the site has a vacancy, a X is appended at the end too.
    """
    sorted_symbol_list = list(set(symbols))
    sorted_symbol_list.sort()  # In-place sort
    name_string = "".join(sorted_symbol_list)
    if has_vacancies(weights):
        name_string += "X"
    return name_string

def set_symbols_and_weights(new_data):
        """Set the chemical symbols and the weights for the site.

        .. note:: Note that the kind name remains unchanged.
        """
        symbols_tuple = _create_symbols_tuple(new_data["symbols"]) if isinstance(new_data["symbols"], str) else new_data["symbols"]
        for symbol in symbols_tuple:
            if symbol not in _valid_symbols:
                raise ValueError(f'This is not a valid element: {symbol}')
        weights_tuple = _create_weights_tuple(new_data["weights"])
        if len(symbols_tuple) != len(weights_tuple):
            raise ValueError('The number of symbols and weights must coincide.')
        validate_symbols_tuple(symbols_tuple)

        validate_weights_tuple(weights_tuple, _SUM_THRESHOLD)
        new_data["alloy"] = symbols_tuple
        new_data["weights"] = weights_tuple

        if "masses" not in new_data.keys() or np.isnan(new_data.get("masses", None)) or new_data.get("masses", None) == 0:
            # Weighted mass
            w_sum = sum(weights_tuple)
            normalized_weights = (i / w_sum for i in weights_tuple)
            element_masses = (_atomic_masses[sym] for sym in symbols_tuple)
            new_data["masses"] = sum(i * j for i, j in zip(normalized_weights, element_masses))

def check_is_alloy(data):
    """Check if the data is an alloy or not.

    :param data: the data to check. The dict of the SiteCore model.
    :return: True if the data is an alloy, False otherwise.
    """
    new_data = copy.deepcopy(data)
    if "weights" not in new_data.keys() or new_data.get("weights", None) is None:
        return new_data
    if len(new_data.get("weight", [1,])) == 1:
        if new_data["symbol"] not in _valid_symbols:
            raise ValueError(f'This is not a valid element: {new_data["symbol"]}')
        return None
    set_symbols_and_weights(new_data)
    return new_data


@calcfunction
def generate_striped_structure(structure: StructureData, to_be_striped: List) -> StructureData:
    """Return a stripped version of the input structure."""
    mutable = structure.get_value()
    for key in to_be_striped:
        mutable = mutable.clear_property(key)
    return StructureData.from_mutable(mutable, detect_kinds=True)


def order_k(k):
    """
    Adjusts the order of elements in the array `k` by ensuring that there are no gaps in the sequence.

    If the minimum value in `k` is 0, it increments all elements by 1. Then, it iterates from the maximum value
    in `k` down to the minimum value, checking if each value minus one is not in `k`. If a value minus one is not
    found, it decrements all elements in `k` that are greater than or equal to the current value.

    Parameters:
    k (numpy.ndarray): An array of integers to be reordered.

    Returns:
    numpy.ndarray: The reordered array `k`.
    """
    if min(k) == 0:
        k = k + 1
    for i in range(max(k),min(1,min(k)),-1):
        if  i-1 not in k:
            k[np.where(k >=i )] -= 1
    return k
