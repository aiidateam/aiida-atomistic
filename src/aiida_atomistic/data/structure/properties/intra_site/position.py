from typing import List
from pydantic import Field

from aiida_atomistic.data.structure.properties.intra_site import IntraSiteProperty

################################################## Start: PBC property:

class Positions(IntraSiteProperty):
    """
    The sites property. 
    """
    #kind_threshold: float = Field(default=1e-3)
    value: List[List[float]] = Field(default=None)
    #kind_tags: List[str] = Field(default=None)
#

################################################## End: PBC property.