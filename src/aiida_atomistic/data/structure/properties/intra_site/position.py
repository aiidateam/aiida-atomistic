from typing import List
from pydantic import Field

from aiida_atomistic.data.structure.properties.intra_site import IntraSiteProperty

################################################## Start: Positions property:

_tolerance_distance = 1e-3 # tolerance to define that two atoms are superimposing. 

class Positions(IntraSiteProperty):
    """
    The sites property. 
    """
    value: List[List[float]] = Field(default=None)
    #kind_tags: List[str] = Field(default=None)
    
    @validator("value", always=True)
    def validate_positions(cls,value,values):
        # (1) validate the list of 3-d coordinates:
        for position in value:
            if len(position) != 3:
                return ValueError("Each position should be represented by an array of length three (x,y,z)")
            
        # (2) check that all positions are unique:
        
################################################## End: Positions property.