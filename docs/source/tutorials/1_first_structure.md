# Creating Your First Structure

In this short tutorial you will learn how to create your first structure, inspect its properties and how to store it in the AiiDA database to then use it in your calculations.

:::{important}
`aiida-atomistic` provides two structure classes:
- **`StructureData`**: Immutable structure for AiiDA provenance (cannot be modified after creation)
- **`StructureBuilder`**: Mutable structure for building and editing, before creating the `StructureData` from it

for more details, please read the [in-depth page on immutability](../in_depth/immutability.md).
:::

## Setting Up

First, let's import the necessary modules and load your AiiDA profile:

```python
from aiida import orm, load_profile
import numpy as np

# Load your AiiDA profile
load_profile()

# Import aiida-atomistic classes
from aiida_atomistic.data import StructureData
```

### From ASE

The quickest way to have our atomistic StructureData is to convert from ASE Atoms objects:

```python
from ase.build import bulk

# Create ASE structure
ase_atoms = bulk('Si', 'diamond', a=5.43)

# Convert to aiida-atomistic
structure = StructureData.from_ase(ase_atoms)
print(f"Converted ASE structure: {structure.properties.formula}")
print(f"Number of sites: {len(structure.sites)}")
```

**Output:**
```
Converted ASE structure: Si2
Number of sites: 2
```

## Exploring Structure Properties

Under the attribute `properties`, the StructureData exposes a variety of useful properties:

```python
# Access basic properties
print(f"Formula: {structure.properties.formula}")
print(f"Cell volume: {structure.properties.cell_volume:.2f} Angstrom^3")
print(f"Number of sites: {len(structure.sites)}")
print(f"Symbols: {structure.properties.symbols}")
```

**Output:**
```
Formula: Si2
Cell volume: 40.03 Angstrom^3
Number of sites: 2
Symbols: ['Si', 'Si']
```

Moreover, it is possible to access each site singularly:

```python
# Loop through sites
for i, site in enumerate(structure.sites):
    print(f"Site {i}: {site.symbol} at {site.position}")
```

**Output:**
```
Site 0: Si at [0. 0. 0.]
Site 1: Si at [1.3575 1.3575 1.3575]
```

Information on the supported and defined properties can be obtained by using the `get_supported_properties` and `get_defined_properties` methods.

You can then store the StructureData in the AiiDA database:

```python
# Store the structure
structure.store()
print(f"Stored with PK: {structure.pk}")

# Load from database
from aiida import orm

loaded = orm.load_node(structure.pk)
print(f"Loaded: {loaded.properties.formula}")
```

**Output:**
```
Stored with PK: 13524
Loaded: Si2
```

## Modifying Structures

For modifications, use `StructureBuilder` (which is the mutable non-AiiDA version of the `StructureData`):

```python
# Import StructureBuilder
from aiida_atomistic.data import StructureBuilder

# Create mutable version
mutable = StructureBuilder.from_ase(ase_atoms)

print(f"Created mutable structure with {len(mutable.sites)} sites")
print(f"Initial first site charge: {mutable.sites[0].charge}")

# Modify existing site
mutable.sites[0].charge = -1.0

print(f"Modified first site charge to {mutable.sites[0].charge}")

# Convert back to immutable for storage
final_structure = StructureData.from_builder(mutable)
```

**Output:**
```
Created mutable structure with 2 sites
Initial first site charge: None
Modified first site charge to -1.0
```
