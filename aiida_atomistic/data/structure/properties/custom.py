from typing import Any
from pydantic import Field

from aiida_atomistic.data.structure.property_utils import BaseProperty

################################################## Start: Template Custom property:

class CustomProperty(BaseProperty):
    """
    Template for custom properties.
    To set it in the StructureData, you need to provide the name of the property in a given format.
    For example:
        structure = StructureData_prototype(
            ase=atoms,
            properties = {
            "pbc": {"value": [True,True,True]},
            "custom_collinear_magnetization": {"value": [1,1,1]},
            },
        ) 
    """
    value: Any = Field()

################################################## End: Template Custom property.