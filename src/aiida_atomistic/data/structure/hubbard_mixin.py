# -*- coding: utf-8 -*-
"""Utility class and functions for HubbardStructureData.
Borrowed and adapted from aiida-quantumespresso
"""
# pylint: disable=no-name-in-module, invalid-name
from typing import List, Literal, Tuple
from pymatgen.core import Lattice, PeriodicSite

import numpy as np

from aiida_quantumespresso.common.hubbard import Hubbard, HubbardParameters

class HubbardGetterMixin:

    def get_hubbard_list(self) -> List[Tuple[int, str, int, str, float, Tuple[int, int, int], str]]:
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
        return [params.to_tuple() for params in self.properties.hubbard.parameters]

class HubbardSetterMixin:

    #@staticmethod
    def set_hubbard_from_list(
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
        self.properties.hubbard = Hubbard(parameters=parameters, projectors=projectors, formulation=formulation)
        return

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
            sites = [
                PeriodicSite(
                    species=site.species,
                    coords=site.coords,
                    lattice=Lattice(self.properties.cell, pbc=self.properties.pbc),
                    coords_are_cartesian=True
                ) for site in self.get_pymatgen_structure().sites
            ]

            if any((atom_index > len(sites) - 1, neighbour_index > len(sites) - 1)):
                raise ValueError(
                    'atom_index and neighbour_index must be within the range of the number of sites in the structure'
                )

            if translation is None:
                _, translation = sites[atom_index].distance_and_image(sites[neighbour_index])
                translation = np.array(translation, dtype=np.int64).tolist()

            hp_tuple = (atom_index, atom_manifold, neighbour_index, neighbour_manifold, value, translation, hubbard_type)
            parameters = HubbardParameters.from_tuple(hp_tuple)
            hubbard = self.properties.hubbard

            if parameters not in hubbard.parameters:
                hubbard.parameters.append(parameters)
                self.properties.hubbard = hubbard

    def pop_hubbard_parameters(self, index: int = -1):
        """Pop Hubbard parameters in the list.

        :param index: index of the Hubbard parameters to pop
        """
        hubbard = self.properties.hubbard
        hubbard.parameters.pop(index) if index != -1 else hubbard.parameters.pop()
        self.properties.hubbard = hubbard

    def clear_hubbard_parameters(self):
        """Clear all the Hubbard parameters."""
        hubbard = self.properties.hubbard
        hubbard.parameters = []
        self.properties.hubbard = hubbard

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
        sites = self.get_pymatgen_structure().sites

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

    def _get_one_kind_index(self, kinds: str) -> List[int]:
        """Return the first site index matching with `kinds`."""
        for i, site in enumerate(self.properties.sites):
            if site.kind_name == kinds:
                return [i]

    def _get_symbol_indices(self, symbol: str) -> List[int]:
        """Return one site index for each kind name matching symbol."""
        matching_kinds = [kind for kind, symbols in zip(self.properties.kind_names,self.properties.symbols)
                          if symbol == symbols]

        return [self.properties.kind_names.index(kind) for kind in matching_kinds]
