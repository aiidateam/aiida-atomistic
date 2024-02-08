from typing import Dict, Any
from pydantic import Extra

from aiida_atomistic.data.structure.properties.property_utils import *

from aiida_atomistic.data.structure.properties.globals.cell import Cell
from aiida_atomistic.data.structure.properties.globals.pbc import Pbc

from aiida_atomistic.data.structure.properties.intra_site.position import Positions
from aiida_atomistic.data.structure.properties.intra_site.symbols import Symbols
from aiida_atomistic.data.structure.properties.intra_site.mass import Mass
from aiida_atomistic.data.structure.properties.intra_site.charge import Charge

from aiida_atomistic.data.structure.properties.custom import CustomProperty

class PropertyCollector(HasPropertyMixin):
    """
    This class is the one used in the StructureData to manage the properties. 
    In principle, it cannot be modified after creation, i.e. is immutable. This respects 
    the `immutability principle` of a StructureData node and requires the creation of a new 
    StructureData instance in case we need to add/update/delete a property.
    
    In the init method, we need also to provide the parent StructureData node, which will have the
    PropertyCollector instance as attribute, and a dictionary with the properties. We then loop on the 
    keys of the properties to initialise all our properties, respecting the rules imposed in each class. 
    
    In principle, we are going to hide every module and information on properties here, in such a way to
    leave as clean as possible the StructureData module.
    
    #### Need of a crystal structure:
    The idea is that we can no more initialise the StructureData without any information, or at least we
    cannot initialise any properties without crystal structure information. This is related to consistency
    checks. 
    So we need some check in the StructureData also, that block or give empty PropertyCollector attribute 
    (StructureData.properties) case no crystal structure is defined.
    
    #### Property format:
    The properties are stored exactly as they are provided in the construction of the class instance: in 
    this way, we do not have ambiguities when the properties are used or loaded from the database/repository.
    To facilitate this, we may provided some `translation methods` from and to the format allowed in the property.
    """
    
    # Supported properties below:
    pbc: Pbc = Property()
    cell: Cell = Property()
    positions: Positions = Property()
    symbols: Symbols = Property()
    mass: Mass = Property()
    charge: Charge = Property()
    custom: CustomProperty = Property()
        
    def __init__(
        self, 
        parent, 
        properties: Dict[str, Dict[str, Any]] = {}):
        
        if not isinstance(properties, dict):
            raise ValueError(f"The `properties` input is not of the right type. Expected '{type(dict())}', received '{type(properties)}'.")
        
        self._parent = parent # Parent StructureData object
        
        # properties: Dictionary containing the properties. The key is the name of the property and the value                                                           
        # is an instance of the corresponding Property subclass value.
        super().__init__()
        
        self._property_attributes = properties
        # Store the properties in the StructureData node.
        #self._parent.base.attributes.set('_property_attributes',{})
        if not self._parent.is_stored:
            self._parent.base.attributes.set('_property_attributes',self._property_attributes)
            
        self._inspect_properties(properties)
    
    
    """def get_supported_properties(self,):
        return list(typing.get_type_hints(self.__class__).keys())
    """
    
    def get_property_attribute(self, key):
        # In AiiDA this could be self.base.attrs['properties'][key] or similar
        return self._property_attributes[key]    
    
    def _inspect_properties(self,properties):
        """
        Method used to understand if we are defining supported/unsupported properties. 
        Here there should be also the detection of custom properties, which 
        have a defined prefix.
        """
        for pname,pvalue in properties.items():
            if pname not in self.get_supported_properties():
                raise NotImplementedError(f"Property '{pname}' is not yet supported.\nSupported properties are: {self.get_supported_properties()}")
            # custom properties:
            #elif pname in self.get_supported_properties():
            #    raise NotImplementedError(f"Property '{pname}' is not yet supported.\nSupported properties are: {self.get_supported_properties()}")
            elif not pvalue:
                raise ValueError(f"Property '{pname}' has not value provided.")
            elif len(pvalue)==0:
                raise ValueError(f"Property '{pname}' is empty.")
            elif not isinstance(pvalue, dict): # maybe to be changed
                raise ValueError(f"The '{pname}' value is not of the right type. Expected '{type(dict())}', received '{type(pvalue)}'.") 
            else:
                """
                Using the pydantic validation:
                the following `getattr` call is done as we want to initialise the properties, in such a way to have `pydantic` validation.
                This is needed because the get method will invoke the `_template_property` method as defined in the 
                `HasPropertyMixin` class.
                The fact is that the `PropertyMixinMetaclass` only define the fget and fset methods, without using them.
                """
                getattr(self,pname)