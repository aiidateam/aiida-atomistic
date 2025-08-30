import copy
import functools
import json
import typing as t
from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field, model_validator, field_serializer
import numpy as np
import warnings

from collections import defaultdict

from aiida import orm
from aiida.common.constants import elements
from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.site import Site, FrozenList, freeze_nested
from aiida_atomistic.data.structure.kind import Kind

from aiida_quantumespresso.common.hubbard import Hubbard

from aiida_atomistic.data.structure import (
    _atomic_masses,
    _DEFAULT_VALUES,
    _DEFAULT_CELL,
    _DEFAULT_PBC,
    _GLOBAL_PROPERTIES,
    _CONVERSION_PLURAL_SINGULAR,
)

class StructureBaseModel(BaseModel):
    """
    A base model representing a structure in atomistic simulations.

    Attributes:
        pbc (Optional[List[bool]]): Periodic boundary conditions in the x, y, and z directions.
        cell (Optional[List[List[float]]]): The cell vectors defining the unit cell of the structure.
    """
    _mutable: t.ClassVar[bool] = True  # class variable to control mutability

    pbc: list[bool] = Field(
        default=_DEFAULT_PBC,
        description="Periodic boundary conditions",
        min_items=3,
        max_items=3,
    )

    cell: t.Union[np.ndarray[float]] = Field(
        default=_DEFAULT_CELL,
        description="Lattice vectors",
        units="Angstrom",
    )

    sites: list[Site] = Field(
        default=None,
        description="List of sites in the structure",
    )

    # global and more specific properties
    tot_magnetization: t.Optional[float] = Field(default=None)
    tot_charge: t.Optional[float] = Field(default=None)
    hubbard: t.Optional[Hubbard] = Field(default=None) #Hubbard(parameters=[]))

    custom: t.Optional[dict] = Field(default=None)

    class Config:
        from_attributes = True
        frozen = False
        arbitrary_types_allowed = True

    @field_validator('cell', mode='before')
    @classmethod
    def validate_cell_shape(cls, v):
        """Ensure cell is always a 3x3 array."""
        v = np.asarray(v)
        v.flags.writeable = cls._mutable
        if v.shape != (3, 3):
            raise ValueError("The cell must be a 3x3 array.")
        return v

    @model_validator(mode='before')
    def check_minimal_requirements(cls, data):
        """
        Validate the minimal requirements of the structure.

        Args:
            data (dict): The input data for the structure. This is automatically passed by pydantic.

        Returns:
            dict: The validated input data.

        Raises:
            ValueError: If the structure does not meet the minimal requirements.
        """

        from aiida_atomistic.data.structure.utils import _check_valid_sites

        if not data.get("sites", None):
            # if no symbols, no positions, we just return the pbc and cell
            return {
                "pbc": data.get("pbc", cls.model_fields["pbc"].default),
                "cell": data.get("cell", cls.model_fields["cell"].default)
            }


        _check_valid_sites(data["sites"])

        return data

    # computed properties
    @computed_field
    def cell_volume(self) -> float:
        """
        Compute the volume of the unit cell.

        Returns:
            float: The volume of the unit cell in cubic Angstroms.
        """
        from aiida_atomistic.data.structure.utils import calc_cell_volume
        return calc_cell_volume(self.cell)

    @computed_field
    def dimensionality(self) -> dict:
        """
        Determine the dimensionality of the structure.

        Returns:
            dict: A dictionary indicating the dimensionality of the structure.
        """
        from aiida_atomistic.data.structure.utils import get_dimensionality
        return get_dimensionality(self.pbc, self.cell)

    @computed_field
    def formula(self) -> str:
        """
        Get the chemical formula of the structure.

        Returns:
            str: The chemical formula of the structure.
        """
        from aiida_atomistic.data.structure.utils import get_formula
        return get_formula(self.sites)

    @computed_field
    def is_alloy(self) -> dict:
        """
        Computed field to determine if the structure is an alloy.
        """
        return  any(_.is_alloy for _ in self.sites)

    @computed_field
    def has_vacancies(self) -> bool:
        """
        Computed field to determine if the structure has vacancies.
        """
        return any(_.has_vacancies for _ in self.sites)

    # HERE I AM DEFINING EXPLICITLY THE COMPUTED FIELDS LIKE POSITIONS AND KINDS, but maybe we can do it with some metaclass.
    @computed_field
    def positions(self) -> np.ndarray:
        """
        Return the positions of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of shape (N, 3) where N is the number of sites.
        """
        if all(site.position is None for site in self.sites):
            return None
        return np.array([site.position for site in self.sites])

    @computed_field
    def kind_names(self) -> t.List[str]:
        """
        Return the list of kind names for all sites in the structure.

        Returns:
            List[str]: A list of kind names corresponding to each site.
        """
        if all(site.kind_name is None for site in self.sites):
            return None
        return [site.kind_name for site in self.sites]

    @computed_field
    def symbols(self) -> t.List[str]:
        """
        Return the list of chemical symbols for all sites in the structure.

        Returns:
            List[str]: A list of chemical symbols corresponding to each site.
        """
        if all(site.symbol is None for site in self.sites):
            return None
        return [site.symbol for site in self.sites]

    @computed_field
    def masses(self) -> np.ndarray:
        """
        Return the masses of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of masses corresponding to each site.
        """
        if all(site.mass is None for site in self.sites):
            return None
        return np.array([site.mass for site in self.sites])

    @computed_field
    def charges(self) -> np.ndarray:
        """
        Return the charges of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of charges corresponding to each site.
        """
        if all(site.charge is None for site in self.sites):
            return None
        return np.array([site.charge for site in self.sites])

    @computed_field
    def magmoms(self) -> np.ndarray:
        """
        Return the magnetic moments of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of magnetic moments corresponding to each site.
        """

        # if all none, return None, otherwise return array with default values if None
        if all(site.magmom is None for site in self.sites):
            return None
        return np.array([site.magmom if site.magmom is not None else _DEFAULT_VALUES['magmom'] for site in self.sites])

    @computed_field
    def magnetizations(self) -> np.ndarray:
        """
        Return the magnetizations of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of magnetizations corresponding to each site.
        """
        if all(site.magnetization is None for site in self.sites):
            return None
        return np.array([site.magnetization for site in self.sites])

    @computed_field
    def weights(self) -> t.List[t.Tuple[float, ...]]:
        """
        Return the weights of all sites in the structure as a list of tuples.

        Returns:
            List[Tuple[float, ...]]: A list of weight tuples corresponding to each site.
        """
        if all(site.weight is None for site in self.sites):
            return None
        return [site.weight for site in self.sites]


    @computed_field
    def kinds(self) -> FrozenList[Kind]:
        """
        Return the reduced set of kinds, grouping sites that share all properties except positions and site_indices.
        """
        # Group sites by their kind-defining properties (excluding positions and site_indices)

        if not self.kind_names:
            #raise ValueError("Kind names must be defined to compute kinds.")
            return None

        kind_map = defaultdict(list)
        for idx, site in enumerate(self.sites):
            # Build a tuple of properties that define a kind (excluding position and site_indices)
            kind_key = (
                site.symbol,
                site.kind_name,
                site.mass,
                site.charge,
                tuple(site.magmom) if isinstance(site.magmom, (list, np.ndarray)) else site.magmom,
                site.magnetization,
                tuple(site.weight) if isinstance(site.weight, (list, np.ndarray)) else site.weight,
                # add other relevant properties here
            )
            kind_map[kind_key].append(idx)

        kinds_list = []
        for kind_key, indices in kind_map.items():
            # Collect positions for all sites of this kind
            positions = np.array([self.positions[i] for i in indices])
            kind = Kind(
                symbol=kind_key[0],
                kind_name=kind_key[1],
                mass=kind_key[2],
                charge=kind_key[3],
                magmom=np.array(kind_key[4]) if kind_key[4] is not None else None,
                magnetization=kind_key[5],
                weight=kind_key[6],
                positions=positions,
                site_indices=indices,
            )
            kinds_list.append(kind)

        return FrozenList(kinds_list)

class MutableStructureModel(StructureBaseModel):
    """
    A mutable structure model that extends the StructureBaseModel class.

    Attributes:
        _mutable (bool): Flag indicating whether the structure is mutable or not.
        sites (List[Site]): List of immutable sites in the structure.
    """

    _mutable = True


class ImmutableStructureModel(StructureBaseModel):
    """
    A class representing an immutable structure model.

    This class inherits from `StructureBaseModel` and provides additional functionality for handling immutable structures.

    Attributes:
        _mutable (bool): Flag indicating whether the structure is mutable or not.
        sites (List[Site]): List of immutable sites in the structure.

    Config:
        from_attributes (bool): Flag indicating whether to load attributes from the input data.
        frozen (bool): Flag indicating whether the model is frozen or not.
        arbitrary_types_allowed (bool): Flag indicating whether arbitrary types are allowed or not.
    """
    _mutable = False

    class Config:
        from_attributes = True
        frozen = True
        arbitrary_types_allowed = True

    def __setattr__(self, key, value):
        # Customizing the exception message when trying to mutate attributes
        if key in self.model_fields:
            raise ValueError("The AiiDA `StructureData` is immutable. You can create a mutable copy of it using its `get_value` method.")
        super().__setattr__(key, value)
