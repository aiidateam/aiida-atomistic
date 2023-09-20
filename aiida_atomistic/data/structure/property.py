"""
Collection of all the classes and metaclasses used to define a
property in the StructureData.    
Requirements for the properties are:
-
-
-
"""
import copy
import functools
import itertools
import json
import typing
from typing import List
from pydantic import BaseModel, Field
from abc import ABCMeta

from aiida.common.constants import elements
from aiida.common.exceptions import UnsupportedSpeciesError

from aiida.orm.nodes.data.data import Data

class BaseProperty(BaseModel):
    # Pydantic2 syntax: #model_config = ConfigDict(frozen=True, extra='forbid')
    parent: Data = Field(
        #init_var=True   # Does not show when dumping the model (but I think it works only in pydantic 2)
        )
    class Config:
        frozen = True
        extra = 'forbid'
        arbitrary_types_allowed = True # You can remove if also StructureData inherits from BaseModel

class Pbc(BaseProperty):
    """
    For now this property is not included in the StructureData. 
    I have doubt on if we really need to move it in the properties. 
    """
    value: List[bool] = Field(min_items=3, max_items=3, default=[False,False,False])
    
    
    def set_from_string(self, dimensionality:str = "3D"):
        if dimensionality=="3D":
            pbc = [True]*3
        elif dimensionality=="0D":
            pbc = [False]*3
        else:
            raise ValueError
        
        return self.parent.set_property(pname='pbc', pvalue={'value':pbc})


class PropertyInfo:
    # Might store the parameters passed to property
    def __init__(self,):
        self.value = None

def Property():
    # If we define parameters, store them in the PropertyInfo
    return PropertyInfo()


class PropertyMixinMetaclass(ABCMeta):

    def __new__(mcs, name, bases, namespace, **kwargs):  # noqa C901
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        # Here we get the properties defined in the typed inputs of the structuredata, and we 
        # take, if any, the attribute provided. This I think in case we initialize the instance with already some properties.
        for attr, type_hint in typing.get_type_hints(cls).items():
            if isinstance(getattr(cls, attr), PropertyInfo):
                assert issubclass(type_hint, BaseProperty)
                cls._valid_properties.append(attr)
                func_get = lambda self, type_hint=type_hint, attr=attr: self._template_property(type_hint=type_hint, attr=attr)
                #I define also a setter, TOTEST if we stay immutable wrt other ways to change the property:
                func_set = lambda self, pname=None, pvalue=None, from_set_property=False: self._set_property(pname, pvalue,from_set_property)
                setattr(cls, attr, property(fget=func_get,fset=func_set))

                #setattr(cls, attr, functools.partialmethod(cls._template_property, type_hint=type_hint, attr=attr))
        return cls            

class HasPropertyMixin(metaclass=PropertyMixinMetaclass):
    _valid_properties = []

    def _template_property(self, type_hint, attr):
        try:
            return type_hint(
                parent=self,
                **self.get_property_attribute(attr)
            )
        except KeyError: #changing this by using type_hints(parent=self) we can initialise properties with the Default value. But I would prefer to set in _property attributes the default... actually it will happen only for PBC. 
            #return None
            return type_hint(
                parent=self,
            )

    def _set_property(self, pname=None, pvalue=None, from_set_property=False):

        if not from_set_property: 
            raise AttributeError("A property can only be set via the set_property() method of StructureData or of the property that you want to change.") 
            
        try:
            #internal check, using the Pydantic initialization.
            type_hint = typing.get_type_hints(self)[pname]
            prop = type_hint(
                parent=self,
                **pvalue
            )
            property_attributes = self.base.attributes.get("_property_attributes").copy()
            property_attributes[pname] = pvalue
            self.base.attributes.set("_property_attributes",property_attributes)
            return
        except KeyError: 
            return None
        
    def get_valid_properties(self):
        # Get the implemented properties
        return self._valid_properties.copy()

    def get_defined_properties(self):
        # Get the properties that you already set
        property_attributes = self.base.attributes.get("_property_attributes")
        return list(set(self.get_valid_properties()).intersection(
            property_attributes.keys()
        ))
        
class StructureMeta(type(HasPropertyMixin), type(Data)):
    """
    This metaclass is need in order to define the inherithance order.
    In particular, the properties require the order type(HasPropertyMixin)-->type(Data),
    so they can be initialised. 
    """
    pass
