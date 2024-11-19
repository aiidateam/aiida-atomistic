import copy
import functools
import json
import typing as t
from pydantic import BaseModel, Field, field_validator, PrivateAttr
import numpy as np
import warnings

from aiida import orm
from aiida.common.constants import elements
from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.models import MutableStructureModel, ImmutableStructureModel
from aiida_atomistic.data.structure.mixin import GetterMixin, SetterMixin

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
_DEFAULT_CELL = ((0, 0, 0),) * 3

_valid_symbols = tuple(i["symbol"] for i in elements.values())
_atomic_masses = {el["symbol"]: el["mass"] for el in elements.values()}
_atomic_numbers = {data["symbol"]: num for num, data in elements.items()}

_default_values = {
    "charges": 0,
    "magmoms": [0, 0, 0],
}

class StructureData(Data, GetterMixin):

    _mutable = False

    def __init__(self, **kwargs):

        if "sites" in kwargs:
            self._properties = ImmutableStructureModel.from_sites_specs(**kwargs)
        else:
            self._properties = ImmutableStructureModel(**kwargs)
        super().__init__()

        defined_properties = self.get_defined_properties().union(self.properties.model_computed_fields.keys()).difference({"sites"}) # exclude the default ones. We do not need to store them into the db.
        for prop, value in self.properties.model_dump(exclude_defaults=True).items():
            if prop in defined_properties:
                self.base.attributes.set(prop, value)

    @property
    def properties(self):
        if self.is_stored:
            return ImmutableStructureModel(**self.base.attributes.all)
        else:
            return self._properties

    @classmethod
    def from_mutable(cls, mutable_structure, detect_kinds: bool = False):
        if not isinstance(mutable_structure, StructureDataMutable):
            raise ValueError(f"Input structure should be of type StructureDataMutable, not {type(mutable_structure)}")
        return cls(**mutable_structure.to_dict(detect_kinds=detect_kinds))

    def get_value(self, detect_kinds: bool = False):
        return StructureDataMutable(**self.to_dict(detect_kinds=detect_kinds))

class StructureDataMutable(GetterMixin, SetterMixin):

    _mutable = True

    def __init__(self, **kwargs):

        if "sites" in kwargs:
            self._properties = MutableStructureModel.from_sites_specs(**kwargs)
        else:
            self._properties = MutableStructureModel(**kwargs)

    @property
    def properties(self):
        return self._properties
