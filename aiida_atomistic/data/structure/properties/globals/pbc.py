from typing import Tuple
from pydantic import Field

from aiida_atomistic.data.structure.properties.property_utils import BaseProperty

################################################## Start: PBC property:

class Pbc(BaseProperty):
    """
    The pbc property. 
    It is different from the pbc attribute directly accessible from the StructureData object.
    """
    domain = "global"
    #kind_threshold: float = Field(default=1e-3)
    value: Tuple[bool,bool,bool] = Field(default=[True,True,True])
    
    @classmethod
    def from_string(cls, dimensionality:str = "3D"):
        """Returns the PBC value base on the inputs dimensionality string.

        Args:
            dimensionality (str, optional): _description_. Defaults to "3D".

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        if dimensionality=="3D":
            pbc_value = [True]*3
        elif dimensionality=="0D":
            pbc_value = [False]*3
        else:
            raise ValueError
        
        return pbc_value

################################################## End: PBC property.