from aiida import load_profile
load_profile()

from pymatgen.core import Structure
from pymatgen.io.cif import CifParser

from aiida_atomistic.data.structure.structure import StructureData
from aiida_atomistic.data.structure.properties.magnetic_qe_utils import MagneticUtils

smag1 = Structure.from_file("./Fe_bcc.mcif", primitive=False) #used for formula and magmom

magmoms = smag1.site_properties["magmom"]
magmom =[list(magmom) for magmom in magmoms]


#### INITIALIZATION
print("\n## Magnetization test ##\n\n")

print("\n## STEP 1: initialization ##")
structure = StructureData(pymatgen=smag1)  #should parse also magmoms here in the future.

print("  magnetization: ",structure.magnetization)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())


print("\n\n### STEP 1: using the built-in 'set_from_components' method and moments as list of arrays ###\n")

magmom = [[1,0,0],[-1,0,0]]


structure.magnetization.set_from_components(magnetic_moment_per_site=magmom)
print("  magnetization: ",structure.magnetization)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())

print("\n\n### STEP 2: using the built-in 'set_from_components' method and moments as list of floats, i.e. collinear ###\n")

magmom = [1,-1]


structure.magnetization.set_from_components(magnetic_moment_per_site=magmom, coordinates = "collinear")
print("  magnetization: ",structure.magnetization)
print("valid: ",structure.get_valid_properties())
print("defined: ",structure.get_defined_properties())

magnetic_card = MagneticUtils(structure).get_magnetic_card()
print(f"QE CARDS are: {magnetic_card}")