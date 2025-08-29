import numpy as np

import typing as t
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

try:
    import ase  # noqa: F401
except ImportError:
    pass

try:
    import pymatgen.core as core  # noqa: F401
except ImportError:
    pass

from plumpy.utils import AttributesFrozendict

from . import (
    _atomic_masses,
    _MAGMOM_THRESHOLD,
    _SUM_THRESHOLD,
    _DEFAULT_VALUES,
    _valid_symbols,
)

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
    ValueError: This list is immutable
    """

    def __setitem__(self, index, value):
        raise ValueError("This list is immutable. Site properties cannot be modified. \
            Please modify them using the `update_site` method of the structure class instance. \
                If your object is the AiiDA immutable `StructureData` object, you can create a mutable copy of it using its `get_value` method.")

class SiteCore(BaseModel):
    """This class contains the core information about a given site of the system.

    It can be a single atom, or an alloy, or even contain vacancies.

    """
    _mutable: t.ClassVar[bool] = False

    model_config = ConfigDict(from_attributes = True,  frozen = False,  arbitrary_types_allowed = True)

    symbol: t.Union[str, t.List[str]]# validation is done in the check_is_alloy
    kind_name: t.Optional[str]
    position: t.Union[np.ndarray[float]] = Field(min_length=3, max_length=3)
    mass: t.Optional[float] = Field(gt=0)
    charge: t.Optional[float] = Field(default=None)
    magmom: t.Optional[np.ndarray[float]] = Field(default=None)
    magnetization: t.Optional[float] = Field(default=None)
    weight: t.Optional[t.Tuple[float, ...]] = Field(default=None)

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
        if "symbol" not in data and cls._mutable.default:
            data["symbol"] = "H"

        # here below we proceed as in the old Kind, where we detect if
        # we have an alloy (i.e. more than one element for the given site)
        alloy_detector = check_is_alloy(data)
        if alloy_detector:
            data.update(alloy_detector)

        #if more than one is specified, between magmoms, magnetizations and tot_magnetization, raise
        if (data.get("magmom", None) is not None) + (data.get("magnetization", None) is not None) > 1:
            raise ValueError(f"You can specify only one between magmom, magnetization: got {data.get('magmom', None)} and {data.get('magnetization', None)}")

        if "mass" not in data:
            data["mass"] = _atomic_masses[data["symbol"]]
        elif not data["mass"]:
            data["mass"] =  _atomic_masses[data["symbol"]]
        #elif data["mass"]<=0:
        #    raise ValueError("The mass of an atom must be positive")

        if "kind_name" not in data:
            data["kind_name"] = data["symbol"]

        return data

    # Start of redundant properties to make easier plugin migrations
    @property
    def kind_name(self):
        return self.kind_name

    @property
    def position(self):
        return self.position
    # End of redundant properties

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
    def atom_to_site(
        cls,
        aseatom: t.Optional[ase.Atom] = None,
        position: t.Optional[list] = None,
        symbol: t.Optional[t.Literal[_valid_symbols]] = None,
        kind_name: t.Optional[str] = None,
        mass: t.Optional[float] = None,
        charge: t.Optional[float] = _DEFAULT_VALUES["charge"],
        magmom: t.Optional[t.List[float]] = _DEFAULT_VALUES["magmom"],
        weight: t.Optional[t.Tuple[float, ...]] = _DEFAULT_VALUES["weight"],
        ) -> dict:
        """Convert an ASE atom or dictionary to a dictionary object which the correct format to describe a Site."""

        if aseatom is not None:
            if position:
                raise ValueError(
                    "If you pass 'aseatom' as a parameter to "
                    "append_atom, you cannot pass any further"
                    "parameter"
                )
            properties_from_Atom = {
                "symbol": aseatom.symbol,
                "kind_name": aseatom.symbol + str(aseatom.tag),
                "position": aseatom.position.tolist(),
                "mass": aseatom.mass,
                "charge": aseatom.charge,
                "magmom": None,
            }
            if not aseatom.charge:
                properties_from_Atom.pop('charge')
            if aseatom.magmom is None:
                properties_from_Atom.pop('magmom')
            elif isinstance(aseatom.magmom, (int, float)):
                properties_from_Atom['magmom'] = [aseatom.magmom, 0, 0]
            else:
                properties_from_Atom['magmom'] = aseatom.magmom

            new_site = cls(**properties_from_Atom)
        else:
            if position is None:
                raise ValueError("You have to specify the position of the new atom")

            if symbol is None:
                raise ValueError("You have to specify the symbol of the new atom")

            # all remaining parameters
            kind_name = symbol if kind_name is None else kind_name
            mass = _atomic_masses[symbol] if mass is None else mass
            weight = _DEFAULT_VALUES["weight"] if weight is None else weight

            new_site = cls(
                symbol=symbol,
                kind_name=kind_name,
                position=position.tolist() if isinstance(position, np.ndarray) else position,
                mass=mass,
                charge=charge,
                magmom=magmom.tolist() if isinstance(magmom, np.ndarray) else magmom
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
        if self.magmom == [0,0,0]:
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

    def to_ase(self, kind_name):
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

        required_properties = set(["symbol", "position", "mass", "charge", "magmom"])

        # we should put a small routine to do tags. or instead of kind_name, provide the tag (or tag mapping).
        tag = None
        atom_dict = self.model_dump()
        atom_dict["symbol"] = atom_dict.pop("symbol", None)
        atom_dict["position"] = atom_dict.pop("position", None)
        atom_dict["magmom"] = atom_dict.pop("magmom", None)
        atom_dict["momentum"] = atom_dict.pop("momenta", None)
        atom_dict["charge"] = atom_dict.pop("charge", None)
        atom_dict["mass"] = atom_dict.pop("mass", None)
        atom_dict["tag"] = atom_dict.pop("kind_name", None)
        for prop in set(self.model_dump().keys()).difference(required_properties):
            atom_dict.pop(prop,None)
        aseatom = ase.Atom(
            **atom_dict
        )

        tag = self.kind_name.replace(self.symbol, "")
        if len(tag) > 0:
            tag = int(tag)
        else:
            tag = 0
        if tag is not None:
            aseatom.tag = tag
        return aseatom

# The Classes which are exposed to the user:
class Site(SiteCore):
    """
    A class representing an immutable site in a crystal structure.

    This class inherits from the `SiteCore` class and adds the functionality to create an immutable site.
    An immutable site cannot be modified once it is created.

    Attributes:
        _mutable (bool): A flag indicating whether the site is mutable or immutable.
    """
    model_config = ConfigDict(from_attributes = True,  frozen = True,  arbitrary_types_allowed = True)

    _mutable = False
