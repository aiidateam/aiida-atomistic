from typing import List, Tuple
from pydantic import Field

from aiida_atomistic.data.structure.properties.property_utils import BaseProperty

################################################## Start: PBC property:

class Positions(BaseProperty):
    """
    The sites property. 
    """
    domain = "per-site"
    #kind_threshold: float = Field(default=1e-3)
    value: List[Tuple[float,float,float]] = Field(default=None)


################################################## End: PBC property.