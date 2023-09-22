# -*- coding: utf-8 -*-
"""Utility class and functions for HubbardStructureData."""
# pylint: disable=no-name-in-module, invalid-name
from typing import List, Literal, Tuple

from pydantic import BaseModel, conint, constr, validator, Field

from aiida_atomistic.data.structure.property import * 


__all__ = ('HubbardParameters', 'Hubbard')


class HubbardParameters(BaseModel):
    """Class for describing onsite and intersite Hubbard interaction parameters.

    .. note: allowed manifold formats are:
            * {N}{L} (2 characters)
            * {N1}{L1}-{N2}{L2} (5 characters)

        N = quantum number (1,2,3,...); L = orbital letter (s,p,d,f,g,h)
    """
    _hubbard_filename = 'hubbard.json'

    atom_index: conint(strict=True, ge=0)
    """Atom index in the abstract structure."""

    atom_manifold: constr(strip_whitespace=True, to_lower=True, min_length=2, max_length=5)
    """Atom manifold (syntax is `3d`, `3d-2p`)."""

    neighbour_index: conint(strict=True, ge=0)
    """Neighbour index in the abstract structure."""

    neighbour_manifold: constr(strip_whitespace=True, to_lower=True, min_length=2, max_length=5)
    """Atom manifold (syntax is `3d`, `3d-2p`)."""

    translation: Tuple[conint(strict=True), conint(strict=True), conint(strict=True)]
    """Translation vector referring to the neighbour atom, (3,) shape list of ints."""

    value: float
    """Value of the Hubbard parameter, expessed in eV."""

    hubbard_type: Literal['Ueff', 'U', 'V', 'J', 'B', 'E2', 'E3']
    """Type of the Hubbard parameters used (`Ueff`, `U`, `V`, `J`, `B`, `E2`, `E3`)."""

    @validator('atom_manifold', 'neighbour_manifold')  # cls is mandatory to use
    def check_manifolds(cls, value):  # pylint: disable=no-self-argument, no-self-use
        """Check the validity of the manifold input.

        Allowed formats are:
            * {N}{L} (2 characters)
            * {N1}{L1}-{N2}{L2} (5 characters)

        N = quantum number (1,2,3,...); L = orbital letter (s,p,d,f,g,h)
        """
        length = len(value)
        if length not in [2, 5]:
            raise ValueError(f'invalid length ``{length}``. Only 2 or 5.')
        if length == 2:
            if not value[0] in [str(_ + 1) for _ in range(6)]:
                raise ValueError(f'invalid quantum number {value[0]}')
            if not value[1] in ['s', 'p', 'd', 'f', 'h']:
                raise ValueError(f'invalid manifold symbol {value[1]}')
        if length == 5:
            if not value[2] == '-':
                raise ValueError(f'the separator {value[0]} is not allowed. Only `-`')
            if not value[3] in [str(_ + 1) for _ in range(6)]:
                raise ValueError(f'the quantum number {value[0]} is not correct')
            if not value[4] in ['s', 'p', 'd', 'f', 'h']:
                raise ValueError(f'the manifold number {value[1]} is not correct')
        return value

    def to_tuple(self) -> Tuple[int, str, int, str, float, Tuple[int, int, int], str]:
        """Return the parameters as a tuple.

        The parameters have the following order:
            * atom_index
            * atom_manifold
            * neighbour_index
            * neighbour_manifold
            * value
            * translationr
            * hubbard_type
        """
        return (
            self.atom_index, self.atom_manifold, self.neighbour_index, self.neighbour_manifold, self.value,
            self.translation, self.hubbard_type
        )

    @staticmethod
    def from_tuple(hubbard_parameters: Tuple[int, str, int, str, float, Tuple[int, int, int], str]):
        """Return a ``HubbardParameters``  instance from a list.

        The parameters within the list must have the following order:
            * atom_index
            * atom_manifold
            * neighbour_index
            * neighbour_manifold
            * value
            * translation
            * hubbard_type
        """
        keys = [
            'atom_index',
            'atom_manifold',
            'neighbour_index',
            'neighbour_manifold',
            'value',
            'translation',
            'hubbard_type',
        ]
        return HubbardParameters(**dict(zip(keys, hubbard_parameters)))


class Hubbard(BaseProperty):
    """Class for complete description of Hubbard interactions."""

    parameters: List[HubbardParameters] = Field(default=None)
    """List of :class:`~aiida_quantumespresso.common.hubbard.HubbardParameters`."""

    projectors: Literal['atomic',
                        'ortho-atomic',
                        'norm-atomic',
                        'wannier-functions',
                        'pseudo-potentials',
                        ] = Field(default=None) #= 'ortho-atomic'
    """Name of the projectors used. Allowed values are:
        'atomic', 'ortho-atomic', 'norm-atomic', 'wannier-functions', 'pseudo-potentials'."""

    formulation: Literal['dudarev', 'liechtenstein'] = Field(default=None) #= 'dudarev'
    """Hubbard formulation used. Allowed values are: 'dudarev', `liechtenstein`."""

    def to_list(self) -> List[Tuple[int, str, int, str, float, Tuple[int, int, int], str]]:
        """Return the Hubbard `parameters` as a list of lists.

        The parameters have the following order within each list:
            * atom_index
            * atom_manifold
            * neighbour_index
            * neighbour_manifold
            * value
            * translation
            * hubbard_type
        """
        return [params.to_tuple() for params in self.parameters]

    def from_list(
        self,
        parameters: List[Tuple[int, str, int, str, float, Tuple[int, int, int], str]],
        projectors: str = 'ortho-atomic',
        formulation: str = 'dudarev',
    ):
        """Return a :meth:`~aiida_quantumespresso.common.hubbard.Hubbard` instance from a list of tuples.

        Each list must contain the hubbard parameters in the following order:
            * atom_index
            * atom_manifold
            * neighbour_index
            * neighbour_manifold
            * value
            * translation
            * hubbard_type
        """
        parameters = [HubbardParameters.from_tuple(value) for value in parameters]
        #return Hubbard(parameters=parameters, projectors=projectors, formulation=formulation)
        return self.parent.set_property(pname='hubbard', pvalue={'parameters':parameters, 'projectors':projectors, 'formulation':formulation})
    
    ### Methods from the HubbardStructureData
    
    def append_hubbard_parameter(
        self,
        atom_index: int,
        atom_manifold: str,
        neighbour_index: int,
        neighbour_manifold: str,
        value: float,
        translation: Tuple[int, int, int] = None,
        hubbard_type: str = 'Ueff',
    ):
        """Append a :class:`~aiida_quantumespresso.common.hubbard.HubbardParameters`.

        :param atom_index: atom index in unitcell
        :param atom_manifold: atomic manifold (e.g. 3d, 3d-2p)
        :param neighbour_index: neighbouring atom index in unitcell
        :param neighbour_manifold: neighbour manifold (e.g. 3d, 3d-2p)
        :param value: value of the Hubbard parameter, in eV
        :param translation: (3,) list of ints, describing the translation vector
            associated with the neighbour atom, defaults to None
        :param hubbard_type: hubbard type (U, V, J, ...), defaults to 'Ueff'
            (see :class:`~aiida_quantumespresso.common.hubbard.Hubbard` for full allowed values)
        """
        pymat = self.parent.get_pymatgen_structure()
        sites = pymat.sites

        if translation is None:
            _, translation = sites[atom_index].distance_and_image(sites[neighbour_index])
            translation = np.array(translation, dtype=np.int64).tolist()

        hp_tuple = (atom_index, atom_manifold, neighbour_index, neighbour_manifold, value, translation, hubbard_type)
        parameters = HubbardParameters.from_tuple(hp_tuple)
        hubbard_parameters = self.parent.hubbard.parameters.copy()

        if parameters not in hubbard_parameters:
            hubbard_parameters.append(parameters)
            return self.parent.set_property(pname='hubbard', pvalue={
                'parameters':hubbard_parameters, 
                'projectors':self.parent.hubbard.projectors, 
                'formulation':self.parent.hubbard.formulation
                })


    def pop_hubbard_parameters(self, index: int):
        """Pop Hubbard parameters in the list.

        :param index: index of the Hubbard parameters to pop
        """
        hubbard_parameters = self.parent.hubbard.parameters.copy()
        hubbard_parameters.pop(index)
        return self.parent.set_property(pname='hubbard', pvalue={
                'parameters':hubbard_parameters, 
                'projectors':self.parent.hubbard.projectors, 
                'formulation':self.parent.hubbard.formulation
                })

    def clear_hubbard_parameters(self):
        """Clear all the Hubbard parameters."""
        hubbard_parameters = self.parent.hubbard.parameters.copy()
        hubbard_parameters = []
        return self.parent.set_property(pname='hubbard', pvalue={
                'parameters':hubbard_parameters, 
                'projectors':self.parent.hubbard.projectors, 
                'formulation':self.parent.hubbard.formulation
                })

    def initialize_intersites_hubbard(
        self,
        atom_name: str,
        atom_manifold: str,
        neighbour_name: str,
        neighbour_manifold: str,
        value: float = 1e-8,
        hubbard_type: str = 'V',
        use_kinds: bool = True,
    ):
        """Initialize and append intersite Hubbard values between an atom and its neighbour(s).

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
        """
        sites = self.parent.get_pymatgen_structure().sites

        function = self._get_one_kind_index if use_kinds else self._get_symbol_indices
        atom_indices = function(atom_name)
        neigh_indices = function(neighbour_name)

        if atom_indices is None or neigh_indices is None:
            raise ValueError('species or kind names not in structure')

        for atom_index in atom_indices:
            for neighbour_index in neigh_indices:
                _, translation = sites[atom_index].distance_and_image(sites[neighbour_index])
                translation = np.array(translation, dtype=np.int64).tolist()
                args = (
                    atom_index, atom_manifold, neighbour_index, neighbour_manifold, value, translation, hubbard_type
                )
                self.append_hubbard_parameter(*args)

    def initialize_onsites_hubbard(
        self,
        atom_name: str,
        atom_manifold: str,
        value: float = 1e-8,
        hubbard_type: str = 'Ueff',
        use_kinds: bool = True,
    ):
        """Initialize and append onsite Hubbard values of atoms with specific name.

        :param atom_name: atom name in unitcell
        :param atom_manifold: atomic manifold (e.g. 3d, 3d-2p)
        :param value: value of the Hubbard parameter, in eV
        :param hubbard_type: hubbard type (U, J, ...), defaults to 'Ueff'
            (see :class:`~aiida_quantumespresso.common.hubbard.Hubbard` for full allowed values)
        :param use_kinds: whether to use kinds for initializing the parameters; when False, it
            initializes all the ``Kinds`` matching the ``atom_name``
        """
        function = self._get_one_kind_index if use_kinds else self._get_symbol_indices
        atom_indices = function(atom_name)

        if atom_indices is None:
            raise ValueError('species or kind names not in structure')

        for atom_index in atom_indices:
            args = (atom_index, atom_manifold, atom_index, atom_manifold, value, [0, 0, 0], hubbard_type)
            self.append_hubbard_parameter(*args)

    def _get_one_kind_index(self, kind_name: str) -> List[int]:
        """Return the first site index matching with `kind_name`."""
        for i, site in enumerate(self.sites):
            if site.kind_name == kind_name:
                return [i]

    def _get_symbol_indices(self, symbol: str) -> List[int]:
        """Return one site index for each kind name matching symbol."""
        site_kindnames = self.parent.get_site_kindnames()
        matching_kinds = [kind.name for kind in self.kinds if symbol in kind.symbol]

        return [site_kindnames.index(kind) for kind in matching_kinds]
