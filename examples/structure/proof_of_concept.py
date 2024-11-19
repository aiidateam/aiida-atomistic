from aiida import load_profile, orm
load_profile()

from aiida_atomistic import StructureData, StructureDataMutable

# ## `StructureData`(s) initialization
#
# As both `StructureData` and `StructureDataMutable` share the same data structure, they also share the same inputs for the constructor: a python dictionary. The format of this dictionary exactly reflects how data are stored in the AiiDA database:

structure_dict = {
    'cell':[[2.75,2.75,0],[0,2.75,2.75],[2.75,0,2.75]],
    'pbc': [True,True,True],
    'sites':[
        {
            'symbols':'Si',
            'position':[3/4, 3/4, 3/4],
        },
        {
            'symbols':'Si',
            'position':[1/2, 1/2, 1/2],
        },
    ],
}

mutable_structure = StructureDataMutable(**structure_dict)
structure = StructureData(**structure_dict)

print("Immutable pbc: ",structure.properties.pbc)
print("Mutable pbc: ",mutable_structure.properties.pbc)

print("Immutable cell: ",structure.properties.cell)
print("Mutable cell: ",mutable_structure.properties.cell)

print("Immutable sites: ",structure.properties.sites)
print("Mutable sites: ",mutable_structure.properties.sites)

print("First immutable site: ",structure.properties.sites[0].dict())
print("First mutable site: ",mutable_structure.properties.sites[0].dict())

# As we provide the `structure_dict` to the constructor of our two structure data classes, it is immediately used to feed the `properties` model. Each site is store as `SiteMutable` (`SiteImmutable`) object for the mutable (immutable) case. Mutability (immutability) is inherited from the corresponding StructureData class used.
#
# The full list of properties can be visualized using the `to_dict` method of the structure:

structure.to_dict()

# %% [markdown]
# We can see that some properties are generated automatically, like *kinds*, *charges*, *dimensionality* and so on, and some other properties are set by default if not provided, e.g. the *kind_name* of each site.
#
# :::{note}
# :class: dropdown
# To visualize the full list of properties, use the `get_supported_properties` method of the structure classes.
#
# The `to_dict` method is nothing else than a wrapper for the *BaseModel* `model_dump` method of the *properties* attribute.
# :::
#
# ### Initialization from ASE or Pymatgen
#
# If we already have an ASE Atoms or a Pymatgen Structure object, we can initialize our StructureData by means of the built-in `from_ase` and `from_pymatgen` methods.
# For ASE:

# %%
from ase.build import bulk
atoms = bulk('Cu', 'fcc', a=3.6)
atoms.set_initial_charges([1,])
atoms.set_tags(["2"])

mutable_structure = StructureDataMutable.from_ase(atoms)
structure = StructureData.from_ase(atoms)

structure.to_dict()

# %% [markdown]
# In the Pymatgen case:

# %%
from pymatgen.core import Lattice, Structure, Molecule

coords = [[0, 0, 0], [0.75,0.5,0.75]]
lattice = Lattice.from_parameters(a=3.84, b=3.84, c=3.84, alpha=120,
                                beta=90, gamma=60)
struct = Structure(lattice, ["Si", "Si"], coords)

struct.sites[0].properties["charge"]=1

mutable_structure = StructureDataMutable.from_pymatgen(struct)
structure = StructureData.from_pymatgen(struct)

mutable_structure.to_dict()

# %% [markdown]
# Moreover, we also provide `to_ase` and `to_pymatgen` methods to obtain the corresponding instances.
#
# ## Passing from StructureData to StructureDataMutable and viceversa
#

# %%
StructureData.from_mutable(mutable_structure) # returns an instance of StructureData
structure.get_value() # returns an instance of StructureDataMutable

# %% [markdown]
#
# ## Mutation of a `StructureData` instance
#
# Let's suppose you want to update some property in the `StructureData` before to use it in a calculation. You cannot. The way to go is either to use ASE or Pymatgen to modify your object and store it back into `StructureData`, or to use the `StructureDataMutable` and its mutation methods, and then convert it into `StructureData`.
# The latter method is the preferred one, as you then have support also for additional properties (to be implemented) like hubbard, which is not supported in ASE and Pymatgen.
#
# `StructureDataMutable` properties can be modified directly, but also the class contains several `set_` methods and more, needed to update a structure. Let's suppose we start from an immutable `StructureData` and we want to update the charges (and the corresponding kinds):

# %%
mutable_structure = structure.get_value()

mutable_structure.set_charges([1, 0])
mutable_structure.set_kind_names(['Si2','Si1'])

new_structure = StructureData.from_mutable(mutable_structure)

print(f"new charges, kinds:\n{new_structure.properties.charges}, {new_structure.properties.kinds}")

# %% [markdown]
# :::{note} Keeping the provenance
# When starting from a `StructureData`, passing to a `StructureDataMutable` and then generating a new modified `StructureData`, we lose provenance. To keep it, we should do the modification by means of an AiiDA [*calcfunction*](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/calculations/concepts.html#calculation-functions), which takes as input(output) the starting(modified) `StructureData`.
# :::

# %% [markdown]
# It is also possible to `add_atom`, `pop_atom`, `update_site` and so on.
# Indeed, we can start from and empty `StructureDataMutable` (i.e., from scratch):

# %%
mutable_structure = StructureDataMutable()
mutable_structure.set_cell([[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]])
mutable_structure.add_atom({
            'symbols':'Si',
            'position':[3/4, 3/4, 3/4],
            'charge': 1,
            'kind_name': 'Si2'
        })

mutable_structure.add_atom({
            'symbols':'Si',
            'position':[1/2, 1/2, 1/2],
            'charge': 0,
            'kind_name': 'Si1'
        })

mutable_structure.to_dict()

# %% [markdown]
# ## Slicing a structure
#
# It is possible to *slice* a structure, i.e. returning only a part of it (in terms of sites). The method returns a new sliced `StructureDataMutable` (`StructureData`) instance.

# %%
sliced_structure = mutable_structure[:1]
sliced_structure.to_dict()

# %% [markdown]
# ## Automatic kinds generation
#
# It is possible to automatically detect kinds when initializing the structure from ASE or Pymatgen. Moreover, the kind can be also generated during the `to_dict` call, such that our output_dictionary will already have the detected kinds. In summary, we can generate our StructureData/StructureDataMutable with automatic kind detection in these three ways:
#
# 1.  new_structuredata = StructureData.from_ase(ase_structure, detect_kinds=True)
# 2.  new_structuredata = StructureData.from_pymatgen(pymatgen_structure, detect_kinds=True)
# 3. new_structuredata = StructureData(**old_structuredata.to_dict(detect_kinds=True))

# %%
Fe_BCC_dictionary = {'pbc': (True, True, True),
        'cell': [[2.8403, 0.0, 1.7391821518091137e-16],
        [-1.7391821518091137e-16, 2.8403, 1.7391821518091137e-16],
        [0.0, 0.0, 2.8403]],
        'sites': [{'symbols': 'Fe',
        'mass': 55.845,
        'position': [0.0, 0.0, 0.0],
        'charge': 0.0,
        'magmom': [2.5, 0.1, 0.1],
        'kind_name': 'Fe'},
        {'symbols': 'Fe',
        'mass': 55.845,
        'position': [1.42015, 1.42015, 1.4201500000000002],
        'charge': 0.0,
        'magmom': [2.4, 0.1, 0.1],
        'kind_name': 'Fe'}]}

mutable_structure = StructureDataMutable(**Fe_BCC_dictionary)

new_mutable_structure = StructureDataMutable(**mutable_structure.to_dict(detect_kinds=True))
new_mutable_structure.to_dict()

# %% [markdown]
# We can also directly put our new sites in the starting `mutable_structure`:

# %%
mutable_structure.clear_sites()
for site in new_mutable_structure.to_dict()['sites']:
    mutable_structure.add_atom(site)

mutable_structure.to_dict()

# %% [markdown]
# ## How to Query StructureData using properties
#
# Thanks to the additional computed properties in our `StructureData` (*formula*, *symbols*, *kinds*, *masses*, *charges*, *magmoms*, *positions*, *cell_volume*, *dimensionality*), we can easily query for a structure:

# %%
from aiida.orm import QueryBuilder

stored = new_StructureData.from_mutable(mutable_structure).store()
print(stored.pk)

qb = QueryBuilder()
qb.append(StructureData,
          filters={'attributes.formula': 'Fe2'},
          )

print(qb.all()[-1])

# %% [markdown]
# ## How to define alloys and deal with vacancies
#
# It is possible to define more than one element for a given site, i.e. to define an *alloy*. This can be done by providing as symbol the combination of the symbols, and also the corresponding *weights* tuple:

# %%
structure  = StructureDataMutable(**{'pbc': [True, True, True],
 'cell': [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]],
 'sites': [{'symbols': 'CuAl',
   'position': [0.0, 0.0, 0.0],
   'weights': (0.5,0.5)
   }],})

structure.properties.sites[0].dict()

# %% [markdown]
# if not provided, the mass is computed accordingly to the symbols and weights. Vacancies are detected when the sum of the weights is less than 1.

# %%
print(structure.is_alloy)
print(structure.has_vacancies)

# %% [markdown]
# ## How to add custom properties
#
# It is possible to add custom properties at the `StructureData` level (not at the `Site` level). To do that, it is sufficient to put the corresponding property under the `custom` Field, a dictionary which should contain the custom property names as keys, followed by the corresponding value:

# %%
structure  = StructureData(**{'pbc': [True, True, True],
 'cell': [[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]],
 'sites': [{'symbols': 'Cu',
   'position': [0.0, 0.0, 0.0],
   }],
 'custom': {
     'electronic_type': 'metal',
 }
 })

structure.properties.custom

# %% [markdown]
# :::{note}
# :class: dropdown
# Automatic serialization of the custom properties is done when the model is dumped (e.g. when the structure is stored in the AiiDA database). If serialization is not possible, an error is retrieved.
# :::

# %% [markdown]
# ## Backward compatibility support
#
# We can use the `to_legacy` method to return the corresponding `orm.StructureData` instance starting from a `StructureData`or `StructureDataMutable` instance, if a given plugin does not yet support the new `StructureData`.
#
