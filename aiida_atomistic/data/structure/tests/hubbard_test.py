from aiida import load_profile
load_profile()

from pymatgen.core import Structure
from pymatgen.io.cif import CifParser

from aiida_atomistic.data.structure.structure import StructureData
from aiida_atomistic.data.structure.hubbard_qe_utils import HubbardUtils

smag1 = Structure.from_file("./Fe_bcc.mcif", primitive=False) #used for formula and magmom

#### INITIALIZATION
print("\n## Hubbard test ##\n\n")

print("\n## STEP 1: initialization ##")
structure = StructureData(pymatgen=smag1) 

print("  hubbard: ",structure.hubbard)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())


print("\n\n### STEP 1: using the built-in 'from_list' method ###\n")

parameters = [
    (0, '3d', 0, '3d', 7.2362, (0, 0, 0), 'V'),
    (0, '3d', 1, '2p', 0.2999, (0, 0, -1), 'V'),
]

structure.hubbard.from_list(parameters=parameters)
print("  hubbard: ",structure.hubbard)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())

print("\n\n### STEP 2: test for the built-in method 'append_hubbard_parameter' ###\n")

structure.hubbard.append_hubbard_parameter(
        atom_index= 1,
        atom_manifold= '3d',
        neighbour_index= 1,
        neighbour_manifold= '3d',
        value= 500,
        translation= (0, 0, 0),
        hubbard_type='V')
print("  hubbard: ",structure.hubbard)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())

hubbard_card = HubbardUtils(structure).get_hubbard_card()
print(f"QE CARDS are: {hubbard_card}")

