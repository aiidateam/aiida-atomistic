import copy
import functools
import json
import typing as t
from pydantic import BaseModel, Field, field_validator, ConfigDict, computed_field, model_validator, field_serializer
import numpy as np
import warnings

from aiida import orm
from aiida.common.constants import elements
from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.site import SiteImmutable, FrozenList, freeze_nested

from aiida_quantumespresso.common.hubbard import Hubbard

try:
    import ase  # noqa: F401
    from ase import io as ase_io

    has_ase = True
    ASE_ATOMS_TYPE = ase.Atoms
except ImportError:
    has_ase = False

    ASE_ATOMS_TYPE = t.Any

try:
    import pymatgen.core as core  # noqa: F401

    has_pymatgen = True
    PYMATGEN_MOLECULE = core.structure.Molecule
    PYMATGEN_STRUCTURE = core.structure.Structure
except ImportError:
    has_pymatgen = False

    PYMATGEN_MOLECULE = t.Any
    PYMATGEN_STRUCTURE = t.Any


_MASS_THRESHOLD = 1.0e-3
# Threshold to check if the sum is one or not
_SUM_THRESHOLD = 1.0e-6
# Default cell
_DEFAULT_CELL = [[0.0, 0.0, 0.0]] * 3
_DEFAULT_PBC = [True, True, True]

_DEFAULT_VALUES = {
    "kinds": "",
    "masses": 0,
    "charges": 0,
    "magmoms": [0, 0, 0],
    "hubbard": None,
    "weights": (1,)
}

_valid_symbols = tuple(i["symbol"] for i in elements.values())
_atomic_masses = {el["symbol"]: el["mass"] for el in elements.values()}
_atomic_numbers = {data["symbol"]: num for num, data in elements.items()}

class StructureBaseModel(BaseModel):
    """
    A base model representing a structure in atomistic simulations.

    Attributes:
        pbc (Optional[List[bool]]): Periodic boundary conditions in the x, y, and z directions.
        cell (Optional[List[List[float]]]): The cell vectors defining the unit cell of the structure.
    """

    pbc: t.Optional[t.List[bool]] = Field(min_length=3, max_length=3, default = _DEFAULT_PBC)
    cell: t.Optional[t.List[t.List[float]]] = Field(default  = _DEFAULT_CELL)
    custom: t.Optional[dict] = Field(default=None)

    symbols: t.Union[t.List[str], t.List[t.List[str]]] = Field(default=[])
    positions: t.List[t.List[float]] = Field(default=[])

    kinds: t.List[str] = Field(default=None)
    weights: t.List[t.Tuple[float, ...]] = Field(default=None)
    masses: t.List[float] = Field(default=None)

    charges: t.List[float] = Field(default=None)
    magmoms: t.List[t.List[float]] = Field(default=None)

    hubbard: t.Optional[Hubbard] = Field(default=Hubbard(parameters=[]))

    class Config:
        from_attributes = True
        frozen = False
        arbitrary_types_allowed = True

    # Making immutable the properties, if needed (i.e. in AiiDA StructureData)
    @field_validator('symbols', 'positions','kinds','magmoms','charges','masses','weights','custom')
    def validate_list(cls, v: t.List[float]) -> t.Any:
        if not cls._mutable.default:
            return freeze_nested(v)
        else:
            return v

    #@field_serializer('positions','magmoms','charges','masses')
    #def serialize_numpy_arrays(cls, v: t.Any) -> t.List:
    #    if isinstance(v, np.ndarray):
    #        return v.tolist()
    #
    #    for index, element  in enumerate(v):
    #        if isinstance(element, np.ndarray):
    #            v[index] = element.tolist()
    #    return v

    @field_validator('pbc')
    @classmethod
    def validate_pbc(cls, v: t.List[bool]) -> t.List[bool]:
        """
        Validate the periodic boundary conditions.

        Args:
            v (List[bool]): The periodic boundary conditions in the x, y, and z directions.

        Returns:
            Any: The validated periodic boundary conditions.

        Raises:
            ValueError: If the periodic boundary conditions are not a list or not of length 3.
        """

        if not isinstance(v, list):
            if cls._mutable.default:
                warnings.warn("pbc should be a list")
            else:
                raise ValueError("pbc must be a list")
            return v

        if len(v) != 3:
            if cls._mutable.default:
                warnings.warn("pbc should be a list of length 3")
            else:
                raise ValueError("pbc must be a list of length 3")
            return v

        if not cls._mutable.default:
            return freeze_nested(v)

        return v

    @field_validator('cell')
    @classmethod
    def validate_cell(cls, v: t.List[t.List[float]]) -> t.List[bool]:
        """
        Validate the cell vectors.

        Args:
            v (List[List[float]]): The cell vectors defining the unit cell of the structure.

        Returns:
            Any: The validated cell vectors.

        Raises:
            ValueError: If the cell vectors are not a list.
        """

        if not isinstance(v, list):
            if cls._mutable.default:
                warnings.warn("cell should be a 3x3 list")
            else:
                raise ValueError("cell must be a 3x3 list")
            return v

        if not cls._mutable.default:
            return freeze_nested(v)

        return v


    @model_validator(mode='before')
    def check_minimal_requirements(cls, data):
        """
        Validate the minimal requirements of the structure.

        Args:
            data (dict): The input data for the structure.

        Returns:
            dict: The validated input data.

        Raises:
            ValueError: If the structure does not meet the minimal requirements.
        """

        from aiida_atomistic.data.structure.utils import _check_valid_sites

        if not data.get("symbols", None):
            return {"pbc":cls.model_fields["pbc"].default, "cell":cls.model_fields["cell"].default}

        if not data.get("positions", None):
            raise ValueError("The structure contains symbols, so it must contain positions also.")

        _check_valid_sites(data["positions"])

        if not data.get("cell", None):
            # raise ValueError("The structure must contain a cell")
            #warnings.warn("using default cell")
            data["cell"] = _DEFAULT_CELL
        if not data.get("pbc", None):
            # raise ValueError("The structure must contain periodic boundary conditions")
            data["pbc"] = [True,True,True]

        # site properties: symbols, kinds, masses, charges, magmoms, weights
        if not data.get("kinds"):
            data["kinds"] = data["symbols"]
        else:
            if len(data["kinds"]) != len(data['symbols']):
                raise ValueError("Length of kinds does not match the number of symbols")
        if "masses" not in data.keys():
            data["masses"] = [_atomic_masses[s] if s in _atomic_masses.keys() else _DEFAULT_VALUES["masses"]
                              for s in data["symbols"]]
        else:
            if len(data["masses"]) != len(data['symbols']):
                raise ValueError("Length of masses does not match the number of symbols")

        for prop in ['positions','charges', 'magmoms', 'weights']:
            if data.get(prop) is None:
                data[prop] = [_DEFAULT_VALUES[prop]] * len(data['symbols'])
            else:
                if len(data[prop]) != len(data['symbols']):
                    raise ValueError(f"Length of {prop} does not match the number of symbols")

        # trying to detect alloys
        if any(mass == 0 for mass in data["masses"]):
            from aiida_atomistic.data.structure.utils import check_is_alloy
            for idx, (symbol, mass, weight) in enumerate(zip(data["symbols"], data["masses"], data["weights"])):
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
                        new_data["kinds"] = symbol
                        new_data["symbols"] = new_data["kinds"]
                        new_data["masses"] = _atomic_masses[symbol] if symbol in _atomic_masses.keys() else _DEFAULT_VALUES["masses"]
                    else:
                        new_data.pop("alloy", None)
                        new_data["kinds"] = ''.join(symbol) if isinstance(symbol, list) else symbol
                        # I could do the following also inside the `check_is_alloy` function, but I do it
                        # here to be more clear on what we do. We provide symbols as joined strings, as the kinds.
                        new_data["symbols"] = new_data["kinds"]
                    for key, value in new_data.items():
                        data[key][idx] = value

        return data

    def validate_instance(self):
        """
        Validate the instance of the structure.

        This method validates the instance attributes of the structure model.

        Raises:
            ValueError: If any of the instance attributes are invalid.
        """

        # Validate minimal requirements
        self.check_minimal_requirements(self.__dict__)
        self.sites
        return

    @computed_field
    def cell_volume(self) -> float:
        """
        Compute the volume of the unit cell.

        Returns:
            float: The volume of the unit cell.
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

    @computed_field # can also be just a property, always frozen... in this way we skip initialization at the structure __init__ phase.
    def sites(self) -> FrozenList[SiteImmutable]:
        """
        Get the sites in the structure.

        Returns:
            FrozenList[SiteImmutable]: The sites in the structure.
        """
        md = self.model_dump(
            exclude=["pbc","cell","custom"]+list(self.model_computed_fields.keys())
            )

        def from_dict_to_list(md):
            transformed_list = [
                {key: value[i] if isinstance(value, list) else _DEFAULT_VALUES[key] for key, value in md.items()}
                for i in range(len(md['symbols']))
            ]

            return transformed_list

        sites = FrozenList([SiteImmutable(**value) for value in from_dict_to_list(md)])
        return sites

    @computed_field
    def formula(self) -> str:
        """
        Get the chemical formula of the structure.

        Returns:
            str: The chemical formula of the structure.
        """
        from aiida_atomistic.data.structure.utils import get_formula
        return get_formula(self.symbols)


    @staticmethod
    def transform_sites_list(sites = [], return_undefined=False):
        fields_list = SiteImmutable.model_fields
        fields_set = set()
        transformed_dict = {k: [] for k in fields_list.keys()}
        for item in sites:
            for key in fields_list.keys():
                transformed_dict[key].append(item[key] if key in item else _DEFAULT_VALUES[key])
                if key not in item and return_undefined:
                    fields_set.add(key)


        return transformed_dict if not return_undefined else fields_set

    @classmethod
    def from_sites_specs(cls, **kwargs):
        if "sites" not in kwargs:
            raise ValueError("The 'sites' key must be present in the input data")

        new_dict = copy.deepcopy(kwargs)
        new_dict.pop("sites")
        transformed_dict = cls.transform_sites_list(kwargs["sites"])
        new_dict.update(transformed_dict)

        return cls(**new_dict)

class MutableStructureModel(StructureBaseModel):
    """
    A mutable structure model that extends the StructureBaseModel class.

    Attributes:
        _mutable (bool): Flag indicating whether the structure is mutable or not.
        sites (List[SiteImmutable]): List of immutable sites in the structure.
    """

    _mutable = True


class ImmutableStructureModel(StructureBaseModel):
    """
    A class representing an immutable structure model.

    This class inherits from `StructureBaseModel` and provides additional functionality for handling immutable structures.

    Attributes:
        _mutable (bool): Flag indicating whether the structure is mutable or not.
        sites (List[SiteImmutable]): List of immutable sites in the structure.

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
