from typing import Tuple
from pydantic import Field

from aiida_atomistic.data.structure.property_utils import BaseProperty

################################################## Start: PBC property:

class Pbc(BaseProperty):
    """
    The pbc property. 
    It is different from the pbc attribute directly accessible from the StructureData object.
    """
    value: Tuple[bool,bool,bool] = Field(default=[True,True,True])
    
    @classmethod
    def from_string(cls, dimensionality:str = "3D"):
        if dimensionality=="3D":
            pbc = [True]*3
        elif dimensionality=="0D":
            pbc = [False]*3
        else:
            raise ValueError
        
        return {'value': pbc}

################################################## End: PBC property.