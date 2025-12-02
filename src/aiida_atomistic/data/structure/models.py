import copy
import functools
import json
import typing as t
from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field, model_validator
import numpy as np
import warnings

from collections import defaultdict

from aiida import orm
from aiida.common.constants import elements
from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.site import Site, FrozenList, freeze_nested, FrozenSite, NumpyArray
from aiida_atomistic.data.structure.kind import Kind

from aiida_quantumespresso.common.hubbard import Hubbard

from aiida_atomistic.data.structure.constants import (
    _atomic_masses,
    _DEFAULT_CELL,
    _DEFAULT_PBC,
    _DEFAULT_VALUES,
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
        min_length=3,
        max_length=3,
    )

    cell: NumpyArray = Field(
        default=_DEFAULT_CELL,
        description="Lattice vectors",
        json_schema_extra={"units": "Angstrom"},
    )

    sites: list[Site] = Field(
        default=[],
        description="List of sites in the structure",
    )

    # global and more specific properties
    tot_magnetization: t.Optional[float] = Field(default=None)
    tot_charge: t.Optional[float] = Field(default=None)
    hubbard: t.Optional[Hubbard] = Field(default=Hubbard(parameters=[])) # to have access to the methods.

    custom: t.Optional[dict] = Field(default=None)

    model_config = ConfigDict(
        from_attributes=True,
        frozen=False,
        arbitrary_types_allowed=True,
        #validate_assignment=True
    )

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
                "cell": data.get("cell", cls.model_fields["cell"].default),
                "sites": []
            }

        # explicitly set default values for pbc and cell if not provided, so in the self.get_defined_properties() they are always there
        for global_property in ['pbc', 'cell']:
            if global_property not in data:
                data[global_property] = cls.model_fields[global_property].default

        return data

    @field_validator('sites', mode='before')
    def validate_sites(cls, v):
        """Validate the list of sites."""
        from aiida_atomistic.data.structure.utils import _check_valid_sites

        if v is None:
            return v
        # else:
        #     # test if they can be converted to Site
        #     sites = [Site.model_validate(site) if not isinstance(site, Site) else site for site in v]

        _check_valid_sites(v)

        return v

    @field_validator('sites', mode='after')
    def freeze_sites(cls, v):
        """Freeze the list of sites if the structure is immutable."""
        if not cls._mutable and v is not None:
            return freeze_nested(v)
        return v

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
        return FrozenList([site.kind_name if site.kind_name is not None else site.symbol for site in self.sites])

    @computed_field
    def symbols(self) -> t.List[str]:
        """
        Return the list of chemical symbols for all sites in the structure.

        Returns:
            List[str]: A list of chemical symbols corresponding to each site.
        """
        if all(site.symbol is None for site in self.sites):
            return None
        return FrozenList([site.symbol for site in self.sites])

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
        return np.array([site.charge if site.charge else _DEFAULT_VALUES['charge'] for site in self.sites])

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
        return np.array([site.magnetization if site.magnetization is not None else _DEFAULT_VALUES['magnetization'] for site in self.sites])

    @computed_field
    def weights(self) -> t.List[t.Tuple[float, ...]]:
        """
        Return the weights of all sites in the structure as a list of tuples.

        Returns:
            List[Tuple[float, ...]]: A list of weight tuples corresponding to each site.
        """
        if all(site.weight is None for site in self.sites):
            return None
        return FrozenList([site.weight if site.weight is not None else _DEFAULT_VALUES['weight'] for site in self.sites])


    @computed_field
    def kinds(self) -> list[Kind]:
        """
        Return the reduced set of kinds, grouping sites that share all properties except positions and site_indices.
        """
        # Group sites by their kind_name. Here there is no kinds validation, just grouping.
        # the validation can be done with the dedicated method validate_kinds

        if not self.kind_names:
            #raise ValueError("Kind names must be defined to access kinds.")
            return None

        # Mapping of kind_name -> site indices
        kind_to_indices = defaultdict(list)
        for i, name in enumerate(self.kind_names):
            kind_to_indices[name].append(i)

        positions_array = self.positions

        kinds_list = []
        seen_kinds = set()

        for site in self.sites:
            kind_name = site.kind_name if site.kind_name else site.symbol

            # Skip if we've already processed this kind
            if kind_name in seen_kinds:
                continue

            seen_kinds.add(kind_name)
            site_indices = kind_to_indices[kind_name]
            positions = positions_array[site_indices]

            kind = Kind(
                **site.model_dump(exclude={'position'}),
                site_indices=site_indices,
                positions=positions,
            )
            kinds_list.append(kind)

        return FrozenList(kinds_list)

    def __repr__(self) -> str:
        """Return a concise string representation of the structure."""
        # Basic info
        nsites = len(self.sites)
        formula = self.formula

        # PBC info
        pbc_dims = sum(self.pbc)
        if pbc_dims == 3:
            pbc_str = "3D"
        elif pbc_dims == 2:
            pbc_str = "2D"
        elif pbc_dims == 1:
            pbc_str = "1D"
        else:
            pbc_str = "0D"

        # Cell volume
        volume = self.cell_volume

        parts = [
            f"formula: {formula}",
            f"sites: {nsites}",
            f"dimensionality: {pbc_str}",
            f"V={volume:.2f} A^3"
        ]

        # Add magnetic info if present
        if self.tot_magnetization is not None:
            parts.append(f"tot_mag={self.tot_magnetization:.2f}")
        elif any(s.magnetization is not None or s.magmom is not None for s in self.sites):
            parts.append("magnetic")

        # Add charge info if present
        if self.tot_charge is not None:
            parts.append(f"tot_charge={self.tot_charge:.2f}")
        elif any(s.charge is not None for s in self.sites):
            parts.append("charged")

        # Add alloy/vacancy info
        if self.is_alloy:
            parts.append("alloy")
        if self.has_vacancies:
            parts.append("vacancies")

        # First line with summary
        repr_str = f" | {', '.join(parts)} |"

        # Add sites info (limit to first 5 sites to avoid too long representations)
        max_sites_to_show = 5
        if nsites > 0:
            repr_str += "\n Sites:"
            for i, site in enumerate(self.sites):
                if i >= max_sites_to_show:
                    repr_str += f"\n  ... (+{nsites - max_sites_to_show} more sites)"
                    break
                repr_str += f"\n  {site}"
            repr_str += "\n"

        return repr_str

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

    pbc: list[bool] = Field(
        default=_DEFAULT_PBC,
        description="Periodic boundary conditions",
        min_length=3,
        max_length=3,
    )

    sites: t.Optional[list[FrozenSite]] = Field(
        default=None,
        description="List of sites in the structure",
    )

    @field_validator('pbc', mode='after')
    @classmethod
    def freeze_pbc(cls, v):
        """Freeze the pbc list to make it immutable."""
        if not isinstance(v, FrozenList):
            return FrozenList(v)
        return v

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
        arbitrary_types_allowed=True,
    )

    def __setattr__(self, key, value):
        # Customizing the exception message when trying to mutate attributes
        if key in self.model_fields:
            raise ValueError("The AiiDA `StructureData` is immutable. You can create a mutable copy of it using its `get_value` method.")
        super().__setattr__(key, value)
