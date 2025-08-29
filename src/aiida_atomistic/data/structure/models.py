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
        can_be_kind_based=False,
        store_in="db",
        min_items=3,
        max_items=3,
        kind_of_property="global",
    )

    cell: t.Union[np.ndarray[float], list[float]] = Field(
        default=_DEFAULT_CELL,
        description="Lattice vectors",
        can_be_kind_based=False,
        units="Angstrom",
        store_in="npz",
        kind_of_property="global",
    )

    ## site properties
    symbols: list[str] = Field(
        default=None,
        description="Chemical symbols of the atoms", # in the db, I can save the set of symbols
        can_be_kind_based=True,
        store_in="json",
        kind_of_property="site",
    )

    positions: t.Union[np.ndarray[float], list[float]] = Field(
        default=None,
        description="3D coordinates of the atoms",
        can_be_kind_based=False,
        units="Angstrom",
        store_in="npz",
        kind_of_property="site",
    )

    kind_names: list[str] = Field(
        default=None,
        description="site-wise list of kinds", # in the db, I can save the set of symbols
        can_be_kind_based=False,
        store_in="json",
        kind_of_property="site",
    )

    magmoms: t.Optional[t.Union[np.ndarray[float], list[float]]] = Field(
        default=None,
        description="3D magnetic moment vector per site",
        can_be_kind_based=True,
        units="Bohr magneton",
        store_in="npz",
        kind_of_property="site",
    )

    magnetizations: t.Optional[t.Union[np.ndarray[float], list[float]]] = Field(
        default=None,
        description="The magnetizations per site. This is a scalar quantity, in contrast to the magmoms which are vectors.",
        can_be_kind_based=True,
        units="Bohr magneton",
        store_in="npz",
        kind_of_property="site",
    )

    charges: t.Optional[t.Union[np.ndarray[float], list[float]]] = Field(
        default=None,
        description="Charge of the atoms",
        can_be_kind_based=True,
        units="e",
        store_in="npz",
        kind_of_property="site",
    )

    masses: t.Union[np.ndarray[float], list[float]] = Field(
        default=None,
        description="Mass of the atoms",
        can_be_kind_based=True,
        store_in="npz",
        kind_of_property="site",
    )
    weights: t.Union[np.ndarray[tuple[float, ...]], list[tuple[float, ...]]] = Field(
        default=None,
        description="weight of the atoms, useful for fractional occupancies",
        can_be_kind_based=True,
        store_in="npz",
        kind_of_property="site",
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

    @field_validator('cell', 'positions', 'magmoms', 'charges', 'masses', 'weights', mode='before') # maybe instead of the explicit list, I can use model_fields.keys()
    @classmethod
    def ensure_numpy_array(cls, v):
        """We want to ensure that the input is a numpy array."""
        if v is None:
            return v
        array_v = np.asarray(v)
        array_v.flags.writeable = cls._mutable
        return array_v

    @field_validator('cell', mode='before')
    @classmethod
    def validate_cell_shape(cls, v):
        """Ensure cell is always a 3x3 array."""
        v = np.asarray(v)
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

        if not data.get("symbols", None):
            # if no symbols, no positions, we just return the pbc and cell
            return {
                "pbc": data.get("pbc", cls.model_fields["pbc"].default),
                "cell": data.get("cell", cls.model_fields["cell"].default)
            }

        if not len(data.get("positions", [])):
            raise ValueError("The structure contains symbols, so it must contain positions also.")

        _check_valid_sites(data["positions"])

        # site properties: symbols, kinds, masses, charges, magmoms, weights
        if data.get("kind_names", None):
            assert len(data["kind_names"]) == len(data['symbols'])

        #if more than one is specified, between magmoms, magnetizations and tot_magnetization, raise
        if (data.get("magmoms", None) is not None) + (data.get("magnetizations", None) is not None) + (data.get("tot_magnetization", None) is not None) > 1:
            raise ValueError("You can specify only one between magmoms, magnetizations and tot_magnetization.")

        if (data.get("charges", None) is not None) + (data.get("tot_charge", None) is not None) > 1:
            raise ValueError("You can specify only one between charges and tot_charge.")

        # do I want to always define masses? maybe not, as they can be derived from the symbols, in case.
        # However I use masses in the alloys detection, so I need to define them here.
        if "masses" not in data.keys():
            data["masses"] = [_atomic_masses[s] if s in _atomic_masses.keys() else _DEFAULT_VALUES["masses"]
                        for s in data["symbols"]]

        for prop in ['positions', 'magmoms', 'charges', 'masses', 'weights']:
            if data.get(prop) is None:
                pass #data[prop] = [_DEFAULT_VALUES[prop]] * len(data['symbols'])
            else:
                if len(data[prop]) != len(data['symbols']):
                    raise ValueError(f"Length of {prop} does not match the number of symbols")

        # trying to detect alloys
        if any(mass == 0 for mass in data["masses"]):
            from aiida_atomistic.data.structure.utils import check_is_alloy
            weights = data.get("weights", [(1,)*len(data["symbols"])])
            for idx, (symbol, mass, weight) in enumerate(zip(data["symbols"], data["masses"], weights)):
                if mass == 0:
                    new_data = check_is_alloy(
                        {
                            "symbols": symbol,
                            "masses": mass,
                            "weights": weight,
                            }
                        )

                    if not new_data: # not an alloy
                        new_data = {}
                        #new_data["kind_names"] = symbol
                        new_data["symbols"] = new_data["kind_names"]
                        new_data["masses"] = _atomic_masses[symbol] if symbol in _atomic_masses.keys() else _DEFAULT_VALUES["masses"]
                    else:
                        new_data.pop("alloy", None)
                        new_data["kind_names"] = ''.join(symbol) if isinstance(symbol, list) else symbol
                        # I could do the following also inside the `check_is_alloy` function, but I do it
                        # here to be more clear on what we do. We provide symbols as joined strings, as the kinds.
                        new_data["symbols"] = new_data["kind_names"]
                    for key, value in new_data.items():
                        data[key][idx] = value

        #if not data.get("weights", None):
        #    data["weights"] = [(1,)*len(data["symbols"])]

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
        return get_formula(self.symbols)

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

    @computed_field # can also be just a property, always frozen... in this way we skip initialization at the structure __init__ phase.
    def sites(self) -> FrozenList[Site]:
        """
        Get the sites in the structure.

        Returns:
            FrozenList[Site]: The sites in the structure.
        """
        md = self.model_dump(
            exclude=_GLOBAL_PROPERTIES+list(self.model_computed_fields.keys())
            )

        convert_to_site_name = lambda s: _CONVERSION_PLURAL_SINGULAR.get(s, s)

        def from_dict_to_list(md):
            transformed_list = [
            {convert_to_site_name(key): value[i] if
                (isinstance(value, list) or isinstance(value, np.ndarray)) else None
            for key, value in md.items()}
            for i in range(len(md['symbols']))
            ]

            return transformed_list

        sites = FrozenList([Site(**value) for value in from_dict_to_list(md)])
        return sites

    @property
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
