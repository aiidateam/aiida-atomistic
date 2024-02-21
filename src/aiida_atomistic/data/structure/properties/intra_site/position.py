from typing import List
from pydantic import Field

from aiida_atomistic.data.structure.properties.intra_site import IntraSiteProperty

################################################## Start: PBC property:

class Positions(IntraSiteProperty):
    """
    The sites property. 
    """
    value: List[List[float]] = Field(default=None)
    #kind_tags: List[str] = Field(default=None)
    
    #add validation for atoms in the same positions.

################################################## End: PBC property.