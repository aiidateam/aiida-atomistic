import numpy as np

import typing as t
import re
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator, BeforeValidator, PlainSerializer, WithJsonSchema
from pydantic_core import core_schema

try:
    import ase  # noqa: F401
except ImportError:
    pass

try:
    import pymatgen.core as core  # noqa: F401
except ImportError:
    pass

from plumpy.utils import AttributesFrozendict

from .constants import (
    _atomic_masses,
    _MAGMOM_THRESHOLD,
    _SUM_THRESHOLD,
    _valid_symbols,
)

# Helper to make numpy arrays work with Pydantic JSON schema
def _validate_array(v):
    """Convert input to numpy array if it isn't already."""
    if isinstance(v, np.ndarray):
        return v
    return np.array(v)

def _serialize_array(v):
    """Serialize numpy array to list."""
    if isinstance(v, np.ndarray):
        return v.tolist()
    return v

# Type alias for numpy arrays that works with Pydantic
NumpyArray = Annotated[
    np.ndarray,
    BeforeValidator(_validate_array),
    PlainSerializer(_serialize_array),
    WithJsonSchema({'type': 'array', 'items': {'type': 'number'}}),
]

def freeze_nested(obj):
    """
    Recursively freezes a nested dictionary or list by converting it into an immutable object.

    Args:
        obj (dict or list): The nested dictionary or list to be frozen.

    Returns:
        AttributesFrozendict or FrozenList: The frozen version of the input object.

    """
    if isinstance(obj, dict):
        return AttributesFrozendict({k: freeze_nested(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return FrozenList(freeze_nested(v) for v in obj)
    else:
        return obj

class FrozenList(list):
    """
    A subclass of list that represents an immutable list.

    This class overrides the __setitem__ method to raise a ValueError
    when attempting to modify the list.

    Usage:
    >>> my_list = FrozenList([1, 2, 3])
    >>> my_list[0] = 4
    ValueError: This list is immutable...
    """

    def __setitem__(self, index, value):
        raise ValueError(
            """
            This list is immutable. Site properties cannot be modified.
            Please modify them using the `set_<property>` method of the structure class instance (where <property> is the plural of the site property name).
            If your object is the AiiDA immutable `StructureData` object, you can create a mutable copy of it using its `get_value` method.
            """
        )

class Site(BaseModel):
    """This class contains the core information about a given site of the system.

    It can be a single atom, or an alloy, or even contain vacancies.

    """
    _mutable: t.ClassVar[bool] = True

    model_config = ConfigDict(
        from_attributes = True,
        frozen = False,
        arbitrary_types_allowed = True,
        validate_assignment = True
        )

    symbol: t.Union[str, t.List[str]]  # validation is done in the check_is_alloy
    position: NumpyArray = Field(
        min_length=3,
        max_length=3,
    )
    mass: t.Optional[float] = Field(
        gt=0,
        json_schema_extra={"threshold": 1e-3, "default": 0}
    )
    charge: t.Optional[float] = Field(
        default=None,
        json_schema_extra={"threshold": 1e-2, "default": 0}
    )
    magmom: t.Optional[NumpyArray] = Field(
        default=None,
        json_schema_extra={"threshold": 1e-2, "default": np.array([0, 0, 0])}
    )
    magnetization: t.Optional[float] = Field(
        default=None,
        json_schema_extra={"threshold": 1e-2, "default": 0}
    )
    weight: t.Optional[t.Tuple[float, ...]] = Field(
        default=None,
        json_schema_extra={"threshold": 1e-2, "default": (1,)}
    )
    kind_name: t.Optional[str] = Field(
        default=None,
        json_schema_extra={"default": ""}
    )


    @field_validator('position', 'magmom', mode='before') # maybe instead of the explicit list, I can use model_fields.keys()
    @classmethod
    def ensure_numpy_array(cls, v):
        """We want to ensure that the input is a numpy array."""
        if v is None:
            return v
        array_v = np.asarray(v)
        array_v.flags.writeable = False
        return array_v


    @model_validator(mode='before')
    def check_minimal_requirements(cls, data):
        from aiida_atomistic.data.structure.utils import check_is_alloy

        # here below we proceed as in the old Kind, where we detect if
        # we have an alloy (i.e. more than one element for the given site)
        alloy_detector = check_is_alloy(data)
        if alloy_detector:
            if "weight" not in data:
                raise ValueError("For alloy sites, the 'weight' property must be specified.")
            data.update(alloy_detector)

        #if more than one is specified, between magmoms, magnetizations and tot_magnetization, raise
        if (data.get("magmom", None) is not None) + (data.get("magnetization", None) is not None) > 1:
            raise ValueError(f"You can specify only one between magmom, magnetization: got {data.get('magmom', None)} and {data.get('magnetization', None)}")

        # we always define masses.
        if "mass" not in data:
            data["mass"] = _atomic_masses[data["symbol"]]
        elif not data["mass"]:
            data["mass"] =  _atomic_masses[data["symbol"]]
        elif data["mass"]<=0:
            raise ValueError("The mass of an atom must be positive")

        # we do not automatically set kind_name!
        #if "kind_name" not in data:
        #    data["kind_name"] = data["symbol"]


        if cls._mutable:
            for prop in data.keys():
                data[prop] = freeze_nested(data[prop])

        return data

    def __repr__(self) -> str:
        """Return a string representation of the Site."""
        symbol_str = self.symbol if isinstance(self.symbol, str) else '/'.join(self.symbol)
        pos_str = f"[{self.position[0]:.3f}, {self.position[1]:.3f}, {self.position[2]:.3f}]"
        parts = [f"{symbol_str} @ {pos_str}"]

        if self.kind_name and self.kind_name != self.symbol:
            parts.append(f"kind={self.kind_name}")
        if self.is_alloy and self.weight:
            weight_str = '/'.join(f"{w:.2f}" for w in self.weight)
            parts.append(f"weight={weight_str}")
        if self.charge is not None:
            parts.append(f"charge={self.charge:.2f}")
        if self.magnetization is not None:
            parts.append(f"magnetization={self.magnetization:.2f}")
        elif self.magmom is not None:
            magmom_str = f"[{self.magmom[0]:.2f}, {self.magmom[1]:.2f}, {self.magmom[2]:.2f}]"
            parts.append(f"magmom={magmom_str}")

        return f"Site({', '.join(parts)})"

    @property
    def is_alloy(self):
        """Return whether the Site is an alloy, i.e. contains more than one element

        :return: boolean, True if the kind has more than one element, False otherwise.
        """
        if self.weight is None:
            return False
        return len(self.weight) != 1

    @property
    def alloy_list(self):
        """Return the list of elements in the given site which is defined as an alloy
        """
        return re.sub( r"([A-Z])", r" \1", self.symbol).split()

    @property
    def has_vacancies(self):
        """Return whether the Structure contains vacancies, i.e. when the sum of the weight is less than one.

        .. note:: the property uses the internal variable `_SUM_THRESHOLD` as a threshold.

        :return: boolean, True if the sum of the weight is less than one, False otherwise
        """
        if self.weight is None:
            return False
        return not 1.0 - sum(self.weight) < _SUM_THRESHOLD

    @classmethod
    def get_default_thresholds(cls) -> dict:
        """Extract default thresholds from field metadata.

        Returns a dictionary mapping property names to their default threshold values
        as defined in the json_schema_extra metadata of each field.

        :return: dictionary with property names as keys and threshold values as floats

        Example:
            >>> Site.get_default_thresholds()
            {'position': 1e-06, 'mass': 0.001, 'charge': 0.0001, 'magmom': 0.01, 'magnetization': 0.01, 'weight': 0.0001}
        """
        thresholds = {}
        for name, field in cls.model_fields.items():
            if field.json_schema_extra and "threshold" in field.json_schema_extra:
                thresholds[name] = field.json_schema_extra["threshold"]
        return thresholds

    @classmethod
    def get_default_values(cls) -> dict:
        """Extract default values from field metadata.

        Returns a dictionary mapping property names to their default values
        as defined in the json_schema_extra metadata of each field.

        :return: dictionary with property names as keys and their default values

        Example:
            >>> Site.get_default_values()
            {'mass': 0, 'charge': 0, 'magmom': array([0, 0, 0]), 'magnetization': 0, 'weight': (1,), 'kind_name': ''}
        """
        defaults = {}
        for name, field in cls.model_fields.items():
            if field.json_schema_extra and "default" in field.json_schema_extra:
                defaults[name] = field.json_schema_extra["default"]
        return defaults

    @classmethod
    def from_ase_atom(
        cls,
        aseatom: t.Optional[ase.Atom] = None,
        tag_to_kind_name: bool = True,
        **kwargs
        ) -> dict:
        """Convert an ASE atom or dictionary to a dictionary object which the correct format to describe a Site."""

        if aseatom is not None:
            if kwargs:
                raise ValueError(
                    "If you pass 'aseatom' as a parameter to "
                    "append_atom, you cannot pass any further"
                    "parameter"
                )
            properties_from_Atom = {
                "symbol": aseatom.symbol,
                "kind_name": aseatom.symbol + str(aseatom.tag).replace('0', ''),
                "position": aseatom.position.tolist(),
                "mass": aseatom.mass,
            }
            if aseatom.charge != 0:
                properties_from_Atom['charge'] = aseatom.charge
            if isinstance(aseatom.magmom, (int, float)):
                if aseatom.magmom != 0:
                    properties_from_Atom['magnetization'] = aseatom.magmom
            elif isinstance(aseatom.magmom, (list, np.ndarray)):
                if np.linalg.norm(aseatom.magmom) > 0:
                    properties_from_Atom['magmom'] = aseatom.magmom

            if not tag_to_kind_name:
                properties_from_Atom.pop("kind_name", None)

            new_site = cls(**properties_from_Atom)
        else:
            new_site = cls(
                **kwargs
            )

        return new_site

    def update(self, **new_data):
        """Update the attributes of the SiteCore instance with new values.

        :param new_data: keyword arguments representing the attributes to be updated
        """
        for field, value in new_data.items():
            setattr(self, field, value)

    def get_magmom_coord(self, coord="spherical"):
        """Get magnetic moment in given coordinate.

        :return: spherical theta and phi in unit rad
                cartesian x y and z in unit ang
        """
        if self.magmom is None:
            return {"starting_magnetization": 0, "angle1": 0, "angle2": 0} if coord == "spherical" else [0, 0, 0]
        elif self.magmom is not None and np.all(self.magmom == 0):
            # array is all zeros
            return {"starting_magnetization": 0, "angle1": 0, "angle2": 0} if coord == "spherical" else [0, 0, 0]

        magmom = self.magmom
        if coord not in ["spherical", "cartesian"]:
            raise ValueError("`coord` can only be `cartesian` or `spherical`")
        if coord == "cartesian":
            magmom_coord = magmom
        else:
            r = np.linalg.norm(magmom)
            if r < _MAGMOM_THRESHOLD:
                magmom_coord = [0.0, 0.0, 0.0]
            else:
                theta = np.arccos(magmom[2]/r) # arccos(z/r)
                theta = theta / np.pi * 180
                phi = np.arctan2(magmom[1], magmom[0]) # atan2(y, x)
                phi = phi / np.pi * 180
                magmom_coord = (r, theta, phi)
                # unit always in degree to fit qe inputs.
        return {"starting_magnetization": magmom_coord[0], "angle1": magmom_coord[1], "angle2": magmom_coord[2]}

    def set_automatic_kind_name(self, tag=None):
        """Set the type to a string obtained with the symbol appended one
        after the other, without spaces, in alphabetical order;
        if the site has a vacancy, a X is appended at the end too.

        :param tag: optional tag to be appended to the kind name
        """
        from aiida_atomistic.data.structure.utils import create_automatic_kind_name
        name_string = create_automatic_kind_name(self.symbol, self.weight)
        if tag is None:
            self.name = name_string
        else:
            self.name = f"{name_string}{tag}"

    def to_ase(self,):
        """Return a ase.Atom object for this site.

        :param kind_name: the list of kind_name from the StructureData object.
        :return: ase.Atom object representing this site
        :raises ValueError: if any site is an alloy or has vacancies
        """
        from collections import defaultdict
        import ase

        # I create the list of tags
        tag_list = []
        used_tags = defaultdict(list)

        #required_properties = set(["symbol", "position", "mass", "charge", "magmom"])

        # we should put a small routine to do tags. or instead of kind_name, provide the tag (or tag mapping).
        tag = None
        atom_dict = self.model_dump()
        atom_dict["symbol"] = atom_dict.pop("symbol", None)
        atom_dict["position"] = atom_dict.pop("position", None)
        magmom = atom_dict.pop("magmom", None)
        atom_dict["magmom"] = atom_dict.pop("magnetization", None) if magmom is None else magmom
        atom_dict["momentum"] = atom_dict.pop("momentum", None)
        atom_dict["charge"] = atom_dict.pop("charge", None)
        atom_dict["mass"] = atom_dict.pop("mass", None)
        atom_dict["tag"] = atom_dict.pop("kind_name", None)

        atom_dict_keys = list(atom_dict.keys())
        for prop in atom_dict_keys:
            if prop not in ["symbol", "position", "mass", "charge", "magmom", "tag"]:
                atom_dict.pop(prop,None)
        aseatom = ase.Atom(
            **atom_dict
        )

        tag = self.kind_name.replace(self.symbol, "") if self.kind_name else None
        if tag is not None:
            if len(tag) > 0:
                tag = int(tag)
            else:
                tag = 0
            aseatom.tag = tag
        return aseatom

class FrozenSite(Site):

    _mutable: t.ClassVar[bool] = False

    model_config = ConfigDict(
        from_attributes = True,
        frozen = True,
        arbitrary_types_allowed = True,
        validate_assignment = True
        )
