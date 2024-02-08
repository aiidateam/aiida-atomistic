from typing import List, Literal
from pydantic import Field, validator, root_validator

from aiida.common.constants import elements

from aiida_atomistic.data.structure.properties.property_utils import BaseProperty


################################################## Start: Charge property:

class Charge(BaseProperty):
    """
    The charge property. 
    """
    domain = "intra-site"
    default_kind_threshold = 0.45
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
            """if len(properties["charge"]["value"]) == 0:
                # assign default values of the charges.
                symbols = values["parent"].base.attributes.get("_property_attributes")["symbols"]
                properties["charge"]["value"] = [_atomic_charges[symbol] for symbol in symbols]
            else:"""
            raise ValueError("The number of provided charges should either be zero or match the number of positions.")
        return value

    
    def to_kinds(self, thr: float = default_kind_threshold, kind_names=False):
        import numpy as np
        """Get the kinds for the charge property

        ### Search algorithm:

        Basically I generate the space grid, using min+thr/2, max+thr/2 and thr. 
        Then, for each point of the space (the max+thr/2 is excluded), 
        I select the sites which are at a distance lower or equal than the thr from the 
        points (which are the middle points of the space [min:max:thr]). 
        In this way I can assign the indexes for each region.

        Then I should provide a renaming of the kinds, 
        but this can be done at the end of the procedure,
        which should be done for every property which requires a kind. 
        Then, I should also consider the tags. 
        
        ## Missing:
        - return the value fo the property, an average: the middle point of the space_grid, or better, 
          the space_grid[i]
        
        Args:
            thr (float, optional): the threshold to consider two atoms of the same element to be the same kind. 
                Defaults to structure.properties.charge.default_kind_threshold.
            kinds_names (bool, optional): if the kinds shoulb be printed also with their element name. When we defined the kinds
                with respect all the properties of the structure, we just use numbers.
            
        Returns:
            kinds: list of kinds associated to the charge property.
        """
        symbols_array = np.array(self.parent.properties.symbols.value)
        prop_array = np.array(self.value)
        space_grid = np.arange(start= np.min(prop_array+thr/2), stop=np.max(prop_array+thr/2),step=thr)

        # list for the value of the property for each generated kind.
        kinds_values = [0]*len(symbols_array)
        
        kinds = list(symbols_array)
        for i in range(len(space_grid)):
            # +thr/1e10 is needed because sometime the equal condition is not detected. 
            indexes = np.where(np.abs(space_grid[i]-prop_array)<=thr/2+thr/1e10)[0]

            if len(indexes) > 0:
                for j in indexes:
                    kinds[j] = kinds[j]+f"{i}" if kind_names else i
                    kinds_values[j] = space_grid[i]
        
        
        return np.array(kinds), kinds_values