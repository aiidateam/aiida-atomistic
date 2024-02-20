import functools
import typing
from typing import List
from pydantic import BaseModel, ConfigDict, Field
import inspect
from abc import ABCMeta

class Data:
    pass

class BaseProperty(BaseModel):
    # Pydantic2 syntax: #model_config = ConfigDict(frozen=True, extra='forbid')
    parent: Data = Field(
        #init_var=True   # Does not show when dumping the model (but I think it works only in pydantic 2)
        )
    class Config:
        frozen = True
        extra = 'forbid'
        arbitrary_types_allowed = True # You can remove if also StructureData inherits from BaseModel

class Magnetization(BaseProperty):
    value: List[float] = Field(default=None)


class Pbc(BaseProperty):
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
            
            self._property_attributes[pname] = pvalue
            return
        except KeyError: 
            return None
        
    def get_valid_properties(self):
        # Get the implemented properties
        return self._valid_properties.copy()

    def get_defined_properties(self):
        # Get the properties that you already set
        return list(set(self.get_valid_properties()).intersection(
            self._property_attributes.keys()
        ))

class StructureData(Data, HasPropertyMixin):
    
    # In AiiDA they go inside an attribute called 'properties'
    # This is an example in which we define only the magnetization and not the pbc.
    
    
    def __init__(self) -> None:
        """
        The '_property_attributes', has to be stored in self., not in cls. as in the first version of the prototype
        Otherwise we have info in the cls, not in the self.
        """
        super().__init__()
        self._property_attributes = {
        #'magnetization': {'moments': [1, -1, 0]},
        #'pbc': {'value':[True,True,True]}
    }

    def get_property_attribute(self, key):
        # In AiiDA this could be self.base.attrs['properties'][key] or similar
        return self._property_attributes[key]    

    ## GP: For some reason however this is recognized by MyPy as a PropertyInfo and not as a Magnetization... one would need to check how pydantic does this
    ## MB: I Think it forces to be a PropertyInfo type as we do not provide inputs at least at the starting phase, in the cls initialization.
    magnetization: Magnetization = Property()
    pbc: Pbc = Property()
    
    def set_property(self, pname=None, pvalue=None):
        
        if not pname in self._valid_properties:
            raise NotImplementedError(f"Property '{pname}' is not yet supported. Use the 'get_valid_properties' method to see the available properties.")
        
        print('Setting {} to {}'.format(pname, str(pvalue)))
        return self._set_property(from_set_property=True, pname=pname, pvalue=pvalue)
    
    
    

#### INITIALIZATION
print("\n## STEP 1: initialization ##")
structure = StructureData()

print("Properties are:")
print("  magnetization: ",structure.magnetization)
print("  pbc: ",structure.pbc)
print("valid properties: ",structure.get_valid_properties())
print("defined properties: ",structure.get_defined_properties())


#### TRYING TO ACCESS DIRECTLY A PROPERTY TO CHANGE IT
### Note that with following Pbc instance is not stored in the structure node.
print("\n\n## STEP 2: trying to change a property by accessing directly ##\n")
pbc = Pbc(value=[True, True, False], parent=structure)

print("### It's read-only, cannot set after init:")
try:
    pbc.value = [False, False, False]
except Exception as exc:
    # cannot store, it's read only!
    print('EXCEPTION:', exc)
else:
    raise AssertionError("Did not raise!")

#### Setting a property in some ways, correct or not.
print("\n\n## STEP 3: setting a property. ##")

print("\n\n### STEP 3.0: setting directly the property doing structure.pbc.value=[True,True,True], then try structure.pbc=1 (incorrect). ###\n")

try:
    structure.pbc.value = [True,False,True]
except Exception as exc:
    # cannot store, it's read only!
    print('\nEXCEPTION:', exc)
else:
    raise AssertionError("Did not raise!")

try:
    structure.pbc = 2
except Exception as exc:
    # cannot store, it's read only!
    print('\nEXCEPTION:', exc)
else:
    raise AssertionError("Did not raise!")


print("\n\n### STEP 3.1: using the set_property method (correct). ###\n")

structure.set_property(pname='pbc', pvalue={'value':[True,False,True]})
print("magnetization: ",structure.magnetization)
print("pbc: ",structure.pbc)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())

print("\n\n### STEP 3.2: using the set_property method but providing wrong accepted input parameters (incorrect). ###\n")

try:
    structure.set_property(pname='pbc', pvalue={'WRONG_PARAMETER':[True,False,True]})
except Exception as exc:
    # cannot store, it's read only!
    print('\nEXCEPTION:', exc)
else:
    raise AssertionError("Did not raise!")

print("\n\n### STEP 3.3: using the set_property method but trying to set a non supported property (incorrect). ###\n")

try:
    structure.set_property(pname='charge', pvalue={'value':[True,False,True]})
except Exception as exc:
    # cannot store, it's read only!
    print('\nEXCEPTION:', exc)
else:
    raise AssertionError("Did not raise!")

print("\n\n### STEP 3.4: using the built-in method of Pbc property (correct). ###\n")

structure.pbc.set_from_string(dimensionality="3D")
print("magnetization: ",structure.magnetization)
print("pbc: ",structure.pbc)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())