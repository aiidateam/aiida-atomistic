from aiida import load_profile
load_profile()

from pymatgen.core import Structure
from pymatgen.io.cif import CifParser

from aiida_atomistic.data.structure.structure_inherit import StructureData
from aiida_atomistic.data.structure.properties.magnetic_qe_utils import MagneticUtils
from aiida_atomistic.data.structure.properties.hubbard_qe_utils import HubbardUtils


smag1 = Structure.from_file("./Fe_bcc.mcif", primitive=False) #used for formula and magmom

magmoms = smag1.site_properties["magmom"]
magmom =[list(magmom) for magmom in magmoms]


#### INITIALIZATION
print("\n## Magnetization+Hubbard test ##\n\n")

structure = StructureData(pymatgen=smag1)  #should parse also magmoms here in the future.

print("defined: ",structure.get_defined_properties())


print("\n\n### STEP 1: first set magnetic, then hubbard ###\n")

magmom = [[1,0,0],[-1,0,0]]
parameters = [
    (0, '3d', 0, '3d', 7.2362, (0, 0, 0), 'V'),
    (0, '3d', 1, '2p', 0.2999, (0, 0, -1), 'V'),
]


structure.magnetization.set_from_components(magnetic_moment_per_site=magmom)
structure.hubbard.from_list(parameters=parameters)

magnetic_card = MagneticUtils(structure).get_magnetic_card()
hubbard_card = HubbardUtils(structure).get_hubbard_card()

print(f"QE Magnetic and Hubbard CARDS are: \n{magnetic_card} \n\n{hubbard_card}")


print("\n\n### STEP 2: first set hubbard, then magnetic ###\n")

structure = StructureData(pymatgen=smag1)  #should parse also magmoms here in the future.


structure.hubbard.from_list(parameters=parameters)
structure.magnetization.set_from_components(magnetic_moment_per_site=magmom)

structure.store()
magnetic_card = MagneticUtils(structure).get_magnetic_card()
hubbard_card = HubbardUtils(structure).get_hubbard_card()

print(f"QE Magnetic and Hubbard CARDS are: \n{magnetic_card} \n\n{hubbard_card}")

print("\n\n==>Check that in both cases the cards are the same.")

