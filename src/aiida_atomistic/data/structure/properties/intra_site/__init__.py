from aiida_atomistic.data.structure.properties.property_utils import BaseProperty

################################################## Start: IntraSiteProperty class:
class IntraSiteProperty(BaseProperty):
    
    """Generic class for intra-site properties. 
    Extends the BaseProperty class with specific methods for the properties which relates to only one site.
    """
    domain = "intra-site"
    
    def to_kinds(self, thr: float = None):
        import numpy as np
        """Get the kinds for a generic intra-site property. Can also be overridden in the specific property.

        ### Search algorithm:

        Basically we compute the indexes array which locates each point in regions centered on our values, considering
        min(values) as reference and each region being of width=thr:
        
            indexes = np.array((prop_array-np.min(prop_array))/thr,dtype=int)
        
        To understand this, try to draw the problem considering prop_array=[1,2,3,4] and thr=0.5.
        This methods allows to efficiently clusterize the point using the defined threshold.
        
        At the end, we reorder the kinds from zero (to have ordered list like Li0, Li1...).
        Basically we define the set of unordered kinds, and the range(len(set(kinds))) being the group of orderd kinds.
        Then we basically do a mapping with the np.where().
        
        Args:
            thr (float, optional): the threshold to consider two atoms of the same element to be the same kind. 
                Defaults to structure.properties.<property>.default_kind_threshold.
                If thr==0, we just return different kind for each site with the original property value. This is 
                needed when we have tags for each site, in the get_kind method of StructureData.
            
        Returns:
            kinds_labels: array of kinds (as integers) associated to the charge property. they are integers so that in the `get_kinds()` method
                             can be used in the matrix representation (the k.T).
            kinds_values: list of the associated property value to each kind detected.
        """ 
        symbols_array = np.array(self.parent.properties.symbols.value)
        prop_array = np.array(self.value)
        
        if not thr: 
            thr = self.default_kind_threshold
        elif thr == 0:
            return np.array(range(len(prop_array))), prop_array
        
        # list for the value of the property for each generated kind.
        kinds_values = np.zeros(len(symbols_array))
        indexes = np.array((prop_array-np.min(prop_array))/thr,dtype=int)
        
        # Here we select the closest value present in the property values
        set_indexes = set(indexes)
        for index in set_indexes:
            where_index_in_indexes = np.where(indexes == index)[0]
            kinds_values[where_index_in_indexes] = np.min(prop_array[where_index_in_indexes])
        
        # here we reorder from zero the kinds.
        list_set_indexes = list(set_indexes)
        kinds_labels = np.zeros(len(symbols_array),dtype=int)
        for i in range(len(list_set_indexes)):
            kinds_labels[np.where(indexes==list_set_indexes[i])[0]] = i
        
        return kinds_labels, kinds_values
################################################## End: IntraSiteProperty class.