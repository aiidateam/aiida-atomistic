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

from aiida_atomistic.data.structure.site import FrozenSite

class Kind(FrozenSite):
    """This class contains the core information about a given kind of the system.

    """
    _mutable: t.ClassVar[bool] = False

    position: t.Union[np.ndarray[float]] = Field(min_length=3, max_length=3, default=None)

    # additional wrt FrozenSite:
    positions: t.Union[np.ndarray[float], list[float]] = Field(default=None)
    site_indices: t.Optional[t.List[int]] = Field(default=None)

    @property
    def name(self) -> str:
        """Return the name of the kind. This is an alias of `kind_name`."""
        return self.kind_name
