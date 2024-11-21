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
            Please modify them using the `update_site` method of the `StructureDataMutable` object. \
                If your object is the AiiDA immutable `StructureData` object, you can create a mutable copy of it using its `get_value` method.")

class SiteCore(BaseModel):
    """This class contains the core information about a given site of the system.

    It can be a single atom, or an alloy, or even contain vacancies.

    """
    model_config = ConfigDict(from_attributes = True,  frozen = False,  arbitrary_types_allowed = True)

    symbols: t.Optional[t.Union[str, t.List[str]]] # validation is done in the check_is_alloy
    kinds: t.Optional[str]
    positions: t.List[float] = Field(min_length=3, max_length=3)
    masses: t.Optional[float] = Field(gt=0)
    charges: t.Optional[float] = Field(default=_DEFAULT_VALUES["charges"])
    magmoms: t.Optional[t.List[float]] = Field(min_length=3, max_length=3, default=_DEFAULT_VALUES["magmoms"])
    weights: t.Optional[t.Tuple[float, ...]] = Field(default=_DEFAULT_VALUES["weights"])

    @field_validator('positions','magmoms')
    def validate_list(cls, v: t.List[float]) -> t.Any:
        if not cls._mutable.default:
            return freeze_nested(v)
        else:
            return v

    @model_validator(mode='before')
    def check_minimal_requirements(cls, data):
        from aiida_atomistic.data.structure.utils import check_is_alloy
        if "symbols" not in data and cls._mutable.default:
            data["symbols"] = "H"

        # here below we proceed as in the old Kind, where we detect if
        # we have an alloy (i.e. more than one element for the given site)
        alloy_detector = check_is_alloy(data)
        if alloy_detector:
            data.update(alloy_detector)

        if "masses" not in data:
            data["masses"] = _atomic_masses[data["symbols"]]
        elif not data["masses"]:
            data["masses"] =  _atomic_masses[data["symbols"]]
        #elif data["masses"]<=0:
        #    raise ValueError("The mass of an atom must be positive")

        if "kinds" not in data:
            data["kinds"] = data["symbols"]

        return data

    @property
    def is_alloy(self):
        """Return whether the Site is an alloy, i.e. contains more than one element

        :return: boolean, True if the kind has more than one element, False otherwise.
        """
        return len(self.weights) != 1

    @property
    def alloy_list(self):
        """Return the list of elements in the given site which is defined as an alloy
        """
        return re.sub( r"([A-Z])", r" \1", self.symbols).split()

    @property
    def has_vacancies(self):
        """Return whether the Structure contains vacancies, i.e. when the sum of the weights is less than one.

        .. note:: the property uses the internal variable `_SUM_THRESHOLD` as a threshold.

        :return: boolean, True if the sum of the weights is less than one, False otherwise
        """
        return not 1.0 - sum(self.weights) < _SUM_THRESHOLD

    @classmethod
    def atom_to_site(
        cls,
        aseatom: t.Optional[ase.Atom] = None,
        positions: t.Optional[list] = None,
        symbols: t.Optional[t.Literal[_valid_symbols]] = None,
        kinds: t.Optional[str] = None,
        masses: t.Optional[float] = None,
        charges: t.Optional[float] = _DEFAULT_VALUES["charges"],
        magmoms: t.Optional[t.List[float]] = _DEFAULT_VALUES["magmoms"],
        weights: t.Optional[t.Tuple[float, ...]] = _DEFAULT_VALUES["weights"],
        ) -> dict:
        """Convert an ASE atom or dictionary to a dictionary object which the correct format to describe a Site."""

        if aseatom is not None:
            if positions:
                raise ValueError(
                    "If you pass 'aseatom' as a parameter to "
                    "append_atom, you cannot pass any further"
                    "parameter"
                )
            properties_from_Atom = {
                "symbols": aseatom.symbol,
                "kinds": aseatom.symbol + str(aseatom.tag),
                "positions": aseatom.position.tolist(),
                "masses": aseatom.mass,
                "charges": aseatom.charge,
                "magmoms": None,
            }
            if not aseatom.charge:
                properties_from_Atom.pop('charges')
            if aseatom.magmom is None:
                properties_from_Atom.pop('magmoms')
            elif isinstance(aseatom.magmom, (int, float)):
                properties_from_Atom['magmoms'] = [aseatom.magmom, 0, 0]
            else:
                properties_from_Atom['magmoms'] = aseatom.magmom

            new_site = cls(**properties_from_Atom)
        else:
            if positions is None:
                raise ValueError("You have to specify the position of the new atom")

            if symbols is None:
                raise ValueError("You have to specify the symbols of the new atom")

            # all remaining parameters
            kinds = symbols if kinds is None else kinds
            masses = _atomic_masses[symbols] if masses is None else masses
            weights = _DEFAULT_VALUES["weights"] if weights is None else weights

            new_site = cls(
                symbols=symbols,
                kinds=kinds,
                positions=positions.tolist() if isinstance(positions, np.ndarray) else positions,
                masses=masses,
                charges=charges,
                magmoms=magmoms.tolist() if isinstance(magmoms, np.ndarray) else magmoms
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
        if self.magmoms == [0,0,0]:
            return {"starting_magnetization": 0, "angle1": 0, "angle2": 0} if coord == "spherical" else [0, 0, 0]

        magmoms = self.magmoms
        if coord not in ["spherical", "cartesian"]:
            raise ValueError("`coord` can only be `cartesian` or `spherical`")
        if coord == "cartesian":
            magmom_coord = magmoms
        else:
            r = np.linalg.norm(magmoms)
            if r < _MAGMOM_THRESHOLD:
                magmom_coord = [0.0, 0.0, 0.0]
            else:
                theta = np.arccos(magmoms[2]/r) # arccos(z/r)
                theta = theta / np.pi * 180
                phi = np.arctan2(magmoms[1], magmoms[0]) # atan2(y, x)
                phi = phi / np.pi * 180
                magmom_coord = (r, theta, phi)
                # unit always in degree to fit qe inputs.
        return {"starting_magnetization": magmom_coord[0], "angle1": magmom_coord[1], "angle2": magmom_coord[2]}

    def set_automatic_kind_name(self, tag=None):
        """Set the type to a string obtained with the symbols appended one
        after the other, without spaces, in alphabetical order;
        if the site has a vacancy, a X is appended at the end too.

        :param tag: optional tag to be appended to the kind name
        """
        from aiida_atomistic.data.structure.utils import create_automatic_kind_name
        name_string = create_automatic_kind_name(self.symbols, self.weights)
        if tag is None:
            self.name = name_string
        else:
            self.name = f"{name_string}{tag}"

    def to_ase(self, kinds):
        """Return a ase.Atom object for this site.

        :param kinds: the list of kinds from the StructureData object.
        :return: ase.Atom object representing this site
        :raises ValueError: if any site is an alloy or has vacancies
        """
        from collections import defaultdict
        import ase

        # I create the list of tags
        tag_list = []
        used_tags = defaultdict(list)

        required_properties = set(["symbols", "positions", "masses", "charges", "magmoms"])

        # we should put a small routine to do tags. or instead of kinds, provide the tag (or tag mapping).
        tag = None
        atom_dict = self.model_dump()
        atom_dict["symbols"] = atom_dict.pop("symbols", None)
        atom_dict["positions"] = atom_dict.pop("positions", None)
        atom_dict["magmom"] = atom_dict.pop("magmoms", None)
        atom_dict["charge"] = atom_dict.pop("charges", None)
        atom_dict["mass"] = atom_dict.pop("masses", None)
        for prop in set(self.model_dump().keys()).difference(required_properties):
            atom_dict.pop(prop,None)
        aseatom = ase.Atom(
            **atom_dict
        )

        tag = self.kinds.replace(self.symbols, "")
        if len(tag) > 0:
            tag = int(tag)
        else:
            tag = 0
        if tag is not None:
            aseatom.tag = tag
        return aseatom

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self!s}>"

    def __str__(self):
        return f"kind name '{self.kinds}' @ {self.positions[0]},{self.positions[1]},{self.positions[2]}"

# The Classes which are exposed to the user:
class SiteMutable(SiteCore):
    """
    A mutable version of the `SiteCore` class.

    This class represents a site in a crystal structure that can be modified.

    Attributes:
        _mutable (bool): Flag indicating if the site is mutable.
    """

    _mutable = True


class SiteImmutable(SiteCore):
    """
    A class representing an immutable site in a crystal structure.

    This class inherits from the `SiteCore` class and adds the functionality to create an immutable site.
    An immutable site cannot be modified once it is created.

    Attributes:
        _mutable (bool): A flag indicating whether the site is mutable or immutable.
    """
    model_config = ConfigDict(from_attributes = True,  frozen = True,  arbitrary_types_allowed = True)

    _mutable = False
