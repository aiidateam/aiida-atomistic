from aiida_atomistic.data.structure.properties.property_utils import BaseProperty

################################################## Start: IntraSiteProperty class:
class IntraSiteProperty(BaseProperty):
    
    """Generic class for intra-site properties. 
    Extends the BaseProperty class with specific methods for the properties which relates to only one site.
    """
    domain = "intra-site"
    
    def to_kinds(self, thr: float = None, kind_names=False):
        import numpy as np
        """Get the kinds for a generic intra-site property

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
        - recognise kind_tags and do not write the same kind; However, the tags should be 
        assigned only in one place for the full structure. no matter the properties. e.g. in the positions.
        - multi-D properties like vectors.
        
        Args:
            thr (float, optional): the threshold to consider two atoms of the same element to be the same kind. 
                Defaults to structure.properties.charge.default_kind_threshold.
            kinds_names (bool, optional): if the kinds shoulb be printed also with their element name. When we defined the kinds
                with respect all the properties of the structure, we just use numbers.
            
        Returns:
            kinds: list of kinds associated to the charge property.
        """
        if not thr: thr = self.default_kind_threshold
        symbols_array = np.array(self.parent.properties.symbols.value)
        prop_array = np.array(self.value)
        space_grid = np.arange(start= np.min(prop_array+thr/2), stop=np.max(prop_array+thr/2),step=thr)
        unshifted_space_grid = np.round(np.arange(start= np.min(prop_array), stop=np.max(prop_array+thr/2),step=thr), countDecimal(thr))

        # list for the value of the property for each generated kind.
        kinds_values = [0]*len(symbols_array)
        
        kinds = list(symbols_array)
        for i in range(len(space_grid)):
            # +thr/1e10 is needed because sometime the equality condition is not detected. 
            indexes = np.where(np.abs(space_grid[i]-prop_array)<=thr/2+thr/1e10)[0]

            if len(indexes) > 0:
                for j in indexes:
                    kinds[j] = kinds[j]+f"{i}" if kind_names else i
                    kinds_values[j] = unshifted_space_grid[i] # space_grid[i]
        
        
        return np.array(kinds), kinds_values


################################################## End: IntraSiteProperty class.

def countDecimal(thr):
    import numpy as np
    """This function counts the decimal digits of a given number.
    Here is used to understand how to round a given property (intra-site domain) value, 
    considering the number of digit of the threshold.
    
    Basically:
    
        log10(thr) = log10(x) + N;
        
        if thr=x*1eN and 1=<x<10:
            N=<log10(thr)<N+1; 
            
        if N is negative: 
            then int(-N) is the number of decimal,
        elif N=>0: 
            we have integers, so we do np.round(number,0)

    Args:
        thr (float, int): the threshold

    Returns:
        round (int): round value, or integer
    """
    round = np.ceil(np.log10(thr))
    return int(-round) if round < 0 else 0