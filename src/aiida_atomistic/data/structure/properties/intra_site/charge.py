from typing import List, Literal
from pydantic import Field, validator, root_validator

from aiida.common.constants import elements

from aiida_atomistic.data.structure.properties.intra_site import IntraSiteProperty


################################################## Start: Charge property:

class Charge(IntraSiteProperty):
    """
    The charge property. 
    """
    default_kind_threshold = 0.1
    # units... maybe specify in the docs.
    value: List[float] = Field(default=None)

    # ToDo:
    @validator("value", always=True)
    def validate_charges(cls,value,values):
        # I have to use the _property_attributes, as accessing directly parent.properties gives recursion error.
        # Maybe it is possible to change how we get the properties? 
        properties = values["parent"].base.attributes.get("_property_attributes")
        if not "positions" in properties:
            # this also validated that we have symbols.
            raise ValueError("If you define charges, you should define also the corresponding positions.")
        elif not len(properties["charge"]["value"]) == len(properties["positions"]["value"]):
            raise ValueError("The number of provided charges should either be zero or match the number of positions.")
        return value
