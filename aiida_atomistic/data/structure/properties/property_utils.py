import typing
from pydantic import BaseModel, Field
from abc import ABCMeta

from aiida import orm


"""
Here we collect utility functions and classes needed to 
enable the properties in the atomistic StructureData type.
"""

######################decorator to allow no calls outside the initialization step: actually, we do not need/use it. 
import inspect

def allow_no_calls_decorator(func):
    """
    This decorator checks if the methods are called 
    from the class, i.e. during the instance creation,
    or via a call which is performed by the user. The
    last way is not allowed. In this way, we essentially 
    protect our code against misuse of the API. 
    For the same reason, WE ALSO do not allow the first way: 
    we are actually deactivating the `set_property` method. 
    We never use it, as we use the `template_property` 
    method in the `StructureData` instance initialization step. 
    
    However, we prefer to leave the `set_property` method there,
    in case in the future we decide to activate it.
    """
    def wrapper(*args, **kwargs):
        frame = inspect.currentframe()

        try:
            locals = frame.f_back.f_locals

            if locals.get('self', None) is args[0]:
                raise NotImplementedError("After the initialization, `properties` and its attributes are read-only!")
                print("Called from this class!")
                func(*args, **kwargs)
            else:
                raise NotImplementedError("This method cannot be called directly!")
        finally:
            pass
    return wrapper

##########################################

################################################## Start: Base Class for a property:
class BaseProperty(BaseModel):
    # Pydantic2 syntax: #model_config = ConfigDict(frozen=True, extra='forbid')
    parent: orm.Data = Field(
        #init_var=True   # Does not show when dumping the model (but I think it works only in pydantic 2)
        )
    
    """
    parent: Data = Field(  #Data is ok if we do not redefine the aiida-core Data class.
        #init_var=True   # Does not show when dumping the model (but I think it works only in pydantic 2)
        )
    """
    class Config:
        frozen = True                  # No changes allowed: immutability
        extra = 'forbid'               # No extra arguments or attributes allowed.
        arbitrary_types_allowed = True # You can remove if also StructureData inherits from BaseModel.


################################################## End: Base Class for a property.


class PropertyInfo:
    # Might store the parameters passed to property
    def __init__(self,):
        self.value = None

def Property():
    # If we define parameters, store them in the PropertyInfo
    return PropertyInfo()


################################################## Start: Mixin classes:

class PropertyMixinMetaclass(ABCMeta):
    
    """
    This class attach the setter and getter method for a property, 
    as defined in the HasPropertyMixin class, respectively with the
    _set_property and _template_property methods. 
    If we use only a constructor for the creation of the StructureData
    together with the properties, we do not need it.
    
    We do not allow to set any property after the creation of the instance: 
    ===> we do not set the `fset` attribute.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):  # noqa C901
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        for attr, type_hint in typing.get_type_hints(cls).items():
            if isinstance(getattr(cls, attr), PropertyInfo):
                assert issubclass(type_hint, BaseProperty)
                cls._valid_properties.add(attr)
                func_get = lambda self, type_hint=type_hint, attr=attr: self._template_property(type_hint=type_hint, attr=attr)
                
                # We do not allow to set any property after the creation of the instance: 
                #===> WE CAN DEACTIVATE THE METHOD, using the `allow_no_calls_decorator`.
                # Here below, we leave it there for now, in case it is needed in the future.
                func_set = lambda self, pname=None, pvalue=None: self._set_property(pname, pvalue)
                setattr(cls, attr, property(fget=func_get,fset=func_set))

        return cls            

class HasPropertyMixin(metaclass=PropertyMixinMetaclass):
    _valid_properties = set()

    def _template_property(self, type_hint, attr):
        try:
            return type_hint(
                parent=self._parent,
                **self.get_property_attribute(attr)
            )
        except: 
            return type_hint(
                parent=self._parent,
            )

    # This function is never used:
    @allow_no_calls_decorator
    def _set_property(self, pname=None, pvalue=None):

        try:
            #internal check, using the Pydantic initialization.
            type_hint = typing.get_type_hints(self)[pname]
            prop = type_hint(
                parent=self._parent,
                **pvalue
            )
            
            self._database_wise_setter(pname, pvalue)
            return
        except KeyError: 
            return None
    
    def _database_wise_setter(self, pname, pvalue):
        property_attributes = self._parent.base.attributes.get("_property_attributes").copy()
        property_attributes[pname] = pvalue
        self._parent.base.attributes.set("_property_attributes",property_attributes)
        return
        
    def get_valid_properties(self):
        # Get the implemented properties
        return self._valid_properties.copy()

    def get_defined_properties(self):
        # Get the properties that you already set
        property_attributes = self._parent.base.attributes.get("_property_attributes")
        return list(set(self.get_valid_properties()).intersection(
            property_attributes.keys()
        ))
        
################################################## End: Mixin classes.
