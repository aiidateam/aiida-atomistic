from typing import List
from pydantic import Field, validator

from aiida_atomistic.data.structure.properties.property_utils import BaseProperty

################################################## Start: PBC property:

class Pbc(BaseProperty):
    """
    The pbc property. 
    It is different from the pbc attribute directly accessible from the StructureData object.
    """
    domain = "global"
    value: List[bool] = Field(default=None, min_items=3,max_items=3)
    
    @validator("value", always=True)
    def validate_pbc(cls,value,values):
        # Here we set the default.
        properties = values["parent"].base.attributes.get("_property_attributes")
        if not value:
            properties = values["parent"].base.attributes.get("_property_attributes")
            properties["pbc"]["value"] = [True,True,True]
            return properties["pbc"]["value"]
                
        return value
    
    @classmethod
    def from_string(cls, dimensionality: str = "3D"):
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