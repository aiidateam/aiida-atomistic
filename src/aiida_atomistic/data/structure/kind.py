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

class Kind(BaseModel):
    """This class contains the core information about a given kind of the system.

    """
    _mutable: t.ClassVar[bool] = True

    model_config = ConfigDict(from_attributes = True,  frozen = True,  arbitrary_types_allowed = True)

    symbol: t.Union[str, t.List[str]]# validation is done in the check_is_alloy
    kind_name: str
    mass: t.Optional[float] = Field(gt=0)
    charge: t.Optional[float] = Field(default=None)
    magmom: t.Optional[np.ndarray[float]] = Field(default=None)
    magnetization: t.Optional[float] = Field(default=None)
    weight: t.Optional[t.Tuple[float, ...]] = Field(default=None)

    # additional wrt site core:
    positions: t.Union[np.ndarray[float], list[float]] = Field(default=None)
    site_indices: t.Optional[t.List[int]] = Field(default=None)


    @field_validator('positions', 'magmom', mode='before') # maybe instead of the explicit list, I can use model_fields.keys()
    @classmethod
    def ensure_numpy_array(cls, v):
        """We want to ensure that the input is a numpy array."""
        if v is None:
            return v
        array_v = np.asarray(v)
        array_v.flags.writeable = False
        return array_v
