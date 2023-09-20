from aiida import load_profile
load_profile()

from aiida_atomistic.data.structure.structure import StructureData, Magnetization

#### INITIALIZATION
print("\n## Hubbard test ##\n\n")

print("\n## STEP 1: initialization ##")
structure = StructureData()

print("  hubbard: ",structure.hubbard)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())


print("\n\n### STEP 1: using the built-in 'from_list' method ###\n")

parameters = [
    (0, '3d', 0, '3d', 7.2362, (0, 0, 0), 'V'),
    (0, '3d', 2, '2p', 0.2999, (-1, 0, -1), 'V'),
    (0, '3d', 1, '2p', 0.2999, (0, 0, -1), 'V'),
    (0, '3d', 1, '2p', 0.2999, (-1, 0, 0), 'V'),
    (0, '3d', 2, '2p', 0.2999, (0, -1, -1), 'V'),
    (0, '3d', 2, '2p', 0.2999, (-1, -1, 0), 'V'),
    #(0, '3d', 1, '2p', 0.2999, (0, -1, 0), 'V')
]

structure.hubbard.from_list(parameters=parameters)
print("  hubbard: ",structure.hubbard)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())

