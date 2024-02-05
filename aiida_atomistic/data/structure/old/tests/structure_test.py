from aiida import load_profile
load_profile()

from aiida_atomistic.data.structure.structure_inherit import StructureData, Magnetization

#### INITIALIZATION
print("\n## STEP 1: initialization ##")
structure = StructureData()

print("Properties are:")
print("  magnetization: ",structure.magnetization)
print(f"pbc: {structure.pbc}... not yet defined as property! By intention.")
print("valid properties: ",structure.get_valid_properties())
print("defined properties: ",structure.get_defined_properties())


#### TRYING TO ACCESS DIRECTLY A PROPERTY TO CHANGE IT
### Note that with following Pbc instance is not stored in the structure node.
print("\n\n## STEP 2: trying to change a property by accessing directly ##\n")
magnetization = Magnetization(value=[1,1,0], parent=structure)

print("### It's read-only, cannot set after init:")
try:
    magnetization.value = [False, False, False]
except Exception as exc:
    # cannot store, it's read only!
    print('EXCEPTION:', exc)
else:
    raise AssertionError("Did not raise!")

#### Setting a property in some ways, correct or not.
print("\n\n## STEP 3: setting a property. ##")

print("\n\n### STEP 3.0: setting directly the property doing structure.magnetization.value=[True,True,True], then try structure.magnetization=1 (incorrect). ###\n")

try:
    structure.magnetization.value = [True,False,True]
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

structure.set_property(pname='magnetization', pvalue={'value':[1,1,1]})
print("magnetization: ",structure.magnetization)
print("pbc: ",structure.pbc)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())

print("\n\n### STEP 3.2: using the set_property method but providing wrong accepted input parameters (incorrect). ###\n")

try:
    structure.set_property(pname='magnetization', pvalue={'WRONG_PARAMETER':[True,False,True]})
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

print("magnetization: ",structure.magnetization)
print("pbc: ",structure.pbc)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())
