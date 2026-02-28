import typing as t
from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field, model_validator
import numpy as np

from collections import defaultdict

from aiida_atomistic.data.structure.site import Site, FrozenList, freeze_nested, FrozenSite, NumpyArray
from aiida_atomistic.data.structure.kind import Kind

from aiida_quantumespresso.common.hubbard import Hubbard


_DEFAULT_CELL = [[0.0, 0.0, 0.0]] * 3
_DEFAULT_PBC = [True, True, True]

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
        json_schema_extra={"store_in": "db", "property_type": "global"},
    )

    cell: NumpyArray = Field(
        default=_DEFAULT_CELL,
        description="Lattice vectors",
        json_schema_extra={"units": "Angstrom", "store_in": "db", "property_type": "global"},
    )

    sites: list[Site] = Field(
        default=[],
        description="List of sites in the structure",
        json_schema_extra={"property_type": "global"},
    )

    # global and more specific properties
    tot_magnetization: t.Optional[float] = Field(default=None, json_schema_extra={"store_in": "db", "property_type": "global"})
    tot_charge: t.Optional[float] = Field(default=None, json_schema_extra={"store_in": "db", "property_type": "global"})
    hubbard: t.Optional[Hubbard] = Field(
        default=Hubbard(parameters=[]),
        json_schema_extra={"store_in": "db", "property_type": "global"},
    )  # to have access to the methods.

    custom: t.Optional[dict] = Field(default=None, json_schema_extra={"store_in": "db", "property_type": "global"})

    model_config = ConfigDict(
        from_attributes=True,
        frozen=False,
        arbitrary_types_allowed=True,
        extra='forbid',
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

    @field_validator('custom', mode='after')
    def freeze_custom(cls, v):
        """Freeze the list of sites if the structure is immutable."""
        if not cls._mutable and v is not None:
            return freeze_nested(v)
        return v

    # computed properties
    @computed_field(json_schema_extra={"store_in": "db"})
    @property
    def cell_volume(self) -> float:
        """
        Compute the volume of the unit cell.

        Returns:
            float: The volume of the unit cell in cubic Angstroms.
        """
        from aiida_atomistic.data.structure.utils import calc_cell_volume
        return calc_cell_volume(self.cell)

    @computed_field(json_schema_extra={"store_in": "db"})
    @property
    def dimensionality(self) -> dict:
        """
        Determine the dimensionality of the structure.

        Returns:
            dict: A dictionary indicating the dimensionality of the structure.
        """
        from aiida_atomistic.data.structure.utils import get_dimensionality
        return get_dimensionality(self.pbc, self.cell)

    @computed_field(json_schema_extra={"store_in": "db"})
    @property
    def formula(self) -> str:
        """
        Get the chemical formula of the structure.

        Returns:
            str: The chemical formula of the structure.
        """
        from aiida_atomistic.data.structure.utils import get_formula
        return get_formula(self.sites)

    @computed_field(json_schema_extra={"store_in": "db"})
    @property
    def is_alloy(self) -> dict:
        """
        Computed field to determine if the structure is an alloy.
        """
        return  any(_.is_alloy for _ in self.sites)

    @computed_field(json_schema_extra={"store_in": "db"})
    @property
    def has_vacancies(self) -> bool:
        """
        Computed field to determine if the structure has vacancies.
        """
        return any(_.has_vacancies for _ in self.sites)

    # HERE I AM DEFINING EXPLICITLY THE COMPUTED FIELDS LIKE POSITIONS AND KINDS, but maybe we can do it with some metaclass.
    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "position"})
    @property
    def positions(self) -> np.ndarray:
        """
        Return the positions of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of shape (N, 3) where N is the number of sites.
        """
        if all(site.position is None for site in self.sites):
            return None
        return np.array([site.position for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "kind_name"})
    @property
    def kind_names(self) -> t.List[str]:
        """
        Return the list of kind names for all sites in the structure.

        Returns:
            List[str]: A list of kind names corresponding to each site.
        """
        if all(site.kind_name is None for site in self.sites):
            return None
        return FrozenList([site.kind_name if site.kind_name is not None else site.symbol for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "symbol"})
    @property
    def symbols(self) -> t.List[str]:
        """
        Return the list of chemical symbols for all sites in the structure.

        Returns:
            List[str]: A list of chemical symbols corresponding to each site.
        """
        if all(site.symbol is None for site in self.sites):
            return None
        return FrozenList([site.symbol for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "mass"})
    @property
    def masses(self) -> np.ndarray:
        """
        Return the masses of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of masses corresponding to each site.
        """
        if all(site.mass is None for site in self.sites):
            return None
        return np.array([site.mass for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "charge"})
    @property
    def charges(self) -> np.ndarray:
        """
        Return the charges of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of charges corresponding to each site.
        """
        if all(site.charge is None for site in self.sites):
            return None
        default_charge = Site.get_default_values().get('charge')
        return np.array([site.charge if site.charge else default_charge for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "magmom"})
    @property
    def magmoms(self) -> np.ndarray:
        """
        Return the magnetic moments of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of magnetic moments corresponding to each site.
        """

        # if all none, return None, otherwise return array with default values if None
        if all(site.magmom is None for site in self.sites):
            return None
        default_magmom = Site.get_default_values().get('magmom')
        return np.array([site.magmom if site.magmom is not None else default_magmom for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "magnetization"})
    @property
    def magnetizations(self) -> np.ndarray:
        """
        Return the magnetizations of all sites in the structure as a numpy array.

        Returns:
            np.ndarray: An array of magnetizations corresponding to each site.
        """
        if all(site.magnetization is None for site in self.sites):
            return None
        default_magnetization = Site.get_default_values().get('magnetization')
        return np.array([site.magnetization if site.magnetization is not None else default_magnetization for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "repository","singular_form": "weight"})
    @property
    def weights(self) -> t.List[t.Tuple[float, ...]]:
        """
        Return the weights of all sites in the structure as a list of tuples.

        Returns:
            List[Tuple[float, ...]]: A list of weight tuples corresponding to each site.
        """
        if all(site.weight is None for site in self.sites):
            return None
        default_weight = Site.get_default_values().get('weight')
        return FrozenList([site.weight if site.weight is not None else default_weight for site in self.sites])


    @computed_field(json_schema_extra={})
    @property
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
                **site.model_dump(exclude={'position','kind_name'}),
                site_indices=site_indices,
                positions=positions,
                kind_name=kind_name
            )
            kinds_list.append(kind)

        return FrozenList(kinds_list)

    # Statistical computed fields for querying
    @computed_field(json_schema_extra={"store_in": "db", "statistic": "max"})
    @property
    def max_charge(self) -> t.Optional[float]:
        """Maximum charge value across all sites."""
        if self.charges is None:
            return None
        return float(np.max(self.charges))

    @computed_field(json_schema_extra={"store_in": "db", "statistic": "min"})
    @property
    def min_charge(self) -> t.Optional[float]:
        """Minimum charge value across all sites."""
        if self.charges is None:
            return None
        return float(np.min(self.charges))

    @computed_field(json_schema_extra={"store_in": "db", "statistic": "max"})
    @property
    def max_magmom(self) -> t.Optional[float]:
        """Maximum magnetic moment magnitude across all sites."""
        if self.magmoms is None:
            return None
        return float(np.max(np.linalg.norm(self.magmoms, axis=1)))

    @computed_field(json_schema_extra={"store_in": "db", "statistic": "min"})
    @property
    def min_magmom(self) -> t.Optional[float]:
        """Minimum magnetic moment magnitude across all sites."""
        if self.magmoms is None:
            return None
        return float(np.min(np.linalg.norm(self.magmoms, axis=1)))

    @computed_field(json_schema_extra={"store_in": "db", "statistic": "max"})
    @property
    def max_magnetization(self) -> t.Optional[float]:
        """Maximum magnetization value across all sites."""
        if self.magnetizations is None:
            return None
        return float(np.max(self.magnetizations))

    @computed_field(json_schema_extra={"store_in": "db", "statistic": "min"})
    @property
    def min_magnetization(self) -> t.Optional[float]:
        """Minimum magnetization value across all sites."""
        if self.magnetizations is None:
            return None
        return float(np.min(self.magnetizations))

    @computed_field(json_schema_extra={"store_in": "db"})
    @property
    def n_sites(self) -> int:
        """Total number of sites in the structure."""
        return len(self.sites)
    
    @computed_field(json_schema_extra={"store_in": "db"})
    @property
    def n_kinds(self) -> int:
        """Total number of sites in the structure."""
        return len(self.kinds) if self.kinds is not None else 0

    def __repr__(self) -> str:
        from pprint import pformat
        pformatted = pformat(self.model_dump())
        return f"StructureModel({pformatted})"

    def __str__(self):
        return self.__repr__()

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
            raise ValueError("The AiiDA `StructureData` is immutable. You can create a mutable copy of it using its `to_builder` method.")
        super().__setattr__(key, value)


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

    sites: t.Optional[list[FrozenSite]] = Field(
        default=None,
        description="List of sites in the structure",
        json_schema_extra={"store_in": "db", "property_type": "global"},
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
