from typing import List, Literal
from pydantic import Field, validator

from aiida.common.constants import elements

from aiida_atomistic.data.structure.properties.intra_site import IntraSiteProperty

################################################## Start: Symbols property:

_valid_symbols = tuple(i['symbol'] for i in elements.values())

class Symbols(IntraSiteProperty):
    """
    The symbols property, intended as the chemical symbols for each atom(site). 
    """
    domain = "intra-site"
    # units... maybe specify in the docs.
    value: List[Literal[_valid_symbols]]
    
    @validator("value", always=True)
    def validate_symbols(cls,value,values):
        # I have to use the _property_attributes, as accessing directly parent.properties gives recursion error.
        # Maybe it is possible to change how we get the properties? 
        properties = values["parent"].base.attributes.get("_property_attributes")
        if not "positions" in properties.keys():
            raise ValueError("If you define symbols, you should define also the corresponding positions.")
        elif not len(value) == len(properties["positions"]["value"]):
            raise ValueError("The number of provided symbols should match the number of positions.")
            # what if we prefer to give a guess? like the following:
            #return [value[0]]*len(values["parent"].base.attributes.get("_property_attributes")["positions"]["value"])
                
        return value
################################################## End: PBC property.