from typing import List
from pydantic import Field

from aiida_atomistic.data.structure.properties.property_utils import BaseProperty

################################################## Start: PBC property:

class Mass(BaseProperty):
    """
    The mass property. 
    """
    domain = "per-site"
    default_kind_threshold: float = Field(default=1e-3)
    # units... maybe specify in the docs.
    value: List[float] = Field(default=None)

    

################################################## End: PBC property.