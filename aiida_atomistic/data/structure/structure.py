from typing import Dict, Any

from aiida_atomistic.data.structure.property_utils import (
    HasPropertyMixin, 
    Property,
    allow_no_calls_decorator, # not really needed as the decorated functions are never used up to now.
)

from aiida_atomistic.data.structure.properties.pbc import Pbc
from aiida_atomistic.data.structure.properties.custom import CustomProperty

from aiida import orm

LegacyStructureData = orm.StructureData

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
    custom: CustomProperty = Property()
    
    def __init__(self, parent, properties: Dict[str, Dict[str, Any]] = {}):
        
        if not isinstance(properties, dict):
            raise ValueError(f"The `properties` input is not of the right type. Expected '{type(dict())}', received '{type(properties)}'.")
        
        self._parent = parent # Parent StructureData object
        
        # properties: Dictionary containing the properties. The key is the name of the property and the value                                                           
        # is an instance of the corresponding Property subclass value.
        super().__init__()
        
        self.inspect_property(properties)
        
        self._property_attributes = properties
        # Store the properties in the StructureData node.
        #self._parent.base.attributes.set('_property_attributes',{})
        self._parent.base.attributes.set('_property_attributes',self._property_attributes)
    
    
    def get_property_attribute(self, key):
        # In AiiDA this could be self.base.attrs['properties'][key] or similar
        return self._property_attributes[key]    
    
    # This function is never used:
    @allow_no_calls_decorator
    def set_property(self, pname=None, pvalue=None):
        
        if not pname in self._valid_properties:
            raise NotImplementedError(f"Property '{pname}' is not yet supported. Use the 'get_valid_properties' method to see the available properties.")
        
        print('Setting {} to {}'.format(pname, str(pvalue)))
        return self._set_property(self,pname=pname, pvalue=pvalue)
    
    def inspect_property(self,properties):
        """
        Method used to understand if we are defining supported/unsupported properties. 
        Here there should be also the detection of custom properties, which 
        have a defined prefix.
        """
        for pname,pvalue in properties.items():
            if pname not in self.get_valid_properties():
                raise NotImplementedError(f"Property '{pname}' is not yet supported.\nSupported properties are: {self.get_valid_properties()}")
            # custom properties:
            #elif pname in self.get_valid_properties():
            #    raise NotImplementedError(f"Property '{pname}' is not yet supported.\nSupported properties are: {self.get_valid_properties()}")
            elif not pvalue:
                raise ValueError(f"Property '{pname}' has not value provided.")
            elif len(pvalue)==0:
                raise ValueError(f"Property '{pname}' is empty.")
            elif not isinstance(pvalue, dict):
                raise ValueError(f"The '{pname}' value is not of the right type. Expected '{type(dict())}', received '{type(pvalue)}'.")
    
    
class StructureData(LegacyStructureData):
    
    """
    Extension of the StructureData class. 
    The main new feature is the possibility to store the properties associated to a given system.
    For example it is possible to store magnetization, hubbard U and V, under the `properties` attribute.
    This attribute is created when the StructureData instance is generated. 
    """
    
    def __init__(
        self, 
        cell=None,
        pbc=None,
        ase=None,
        pymatgen=None,
        pymatgen_structure=None,
        pymatgen_molecule=None,
        properties: Dict[str, Dict[str, Any]] = {},
        **kwargs,) -> None:
        """
        The '_property_attribute', has to be stored in self., not in cls. as in the first version of the prototype
        Otherwise we have info in the cls, not in the self.
        """
        if not isinstance(properties, dict):
            raise ValueError(f"The `properties` input is not of the right type. Expected '{type(dict())}', received '{type(properties)}'.")
        
        super().__init__(
            cell,
            pbc,
            ase,
            pymatgen,
            pymatgen_structure,
            pymatgen_molecule,
            **kwargs,
        )
        
        # Private property attribute
        self._property_attribute = PropertyCollector(parent=self, properties=properties)
    
    # Setting the properties attribute as immutable.
    # The only drawback is that the `_properties_attribute` one can still be modified. 
    @property
    def properties(self):
        return self._property_attribute

    @properties.setter
    def properties(self,value):
        raise AttributeError("After the initialization, `properties` is a read-only attribute")
    
        