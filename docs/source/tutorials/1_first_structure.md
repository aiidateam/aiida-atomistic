# Creating Your First Structure

In this short tutorial you will learn how to create your first structure, inspect its properties and how to store it in the AiiDA database to then use it in your calculations.

## Setting Up

First, let's import the necessary modules and load your AiiDA profile:

```python
from aiida import orm, load_profile
import numpy as np

# Load your AiiDA profile
load_profile()

# Import aiida-atomistic classes
from aiida_atomistic.data import StructureData, StructureDataMutable
```

### From ASE

The quickest way to have our atomistic StructureData is to convert from ASE Atoms objects:

```python
from ase.build import bulk

# Create ASE structure
ase_atoms = bulk('Si', 'diamond', a=5.43)

# Convert to aiida-atomistic
structure = StructureData.from_ase(ase_atoms, detect_kinds=True)
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
Cell volume: 40.04 Angstrom^3
Number of sites: 2
Symbols: ['Si', 'Si']
```
Moreover, it is possible to access each site:

```python
# Loop through sites
for i, site in enumerate(structure.sites):
    print(f"Site {i}: {site.symbol} at {site.position}")
```

**Output:**
```
Site 0: Si at [0. 0. 0.]
Site 1: Si at [3.84 1.35764502 1.92]
```

Information on the supported properties can be obtained by using the `get_supported_properties` method:

```python
# Get all supported properties
supported = structure.get_supported_properties()
print(f"Supported properties: {supported}")

# Get defined properties in this structure
defined = structure.get_defined_properties()
print(f"Defined properties: {defined}")
```

**Output:**
```
Positions shape: (2, 3)
Supported properties: {'global': {'tot_magnetization', 'custom', 'sites', 'tot_charge', 'pbc', 'hubbard', 'cell'}, 'site': {'mass', 'weight', 'kind_name', 'magnetization', 'charge', 'symbol', 'position', 'magmom'}}
Defined properties: {'masses', 'positions', 'symbols', 'sites', 'pbc', 'cell'}
```

## Modifying Structures

For modifications, use `StructureDataMutable` (which is the mutable non-AiiDA version of the `StructureData`):

```python
# Create mutable version
mutable = StructureDataMutable.from_ase(ase_atoms)

print(f"Created mutable structure with {len(mutable.sites)} sites")
print(f"Initial first site charge: {mutable.sites[0].charge}")

# Modify existing site
mutable.sites[0].charge = -1.0

print(f"Modified first site charge to {mutable.sites[0].charge}")

# Convert back to immutable for storage
final_structure = StructureData.from_mutable(mutable)
```

**Output:**
```
Created mutable structure with 2 sites
Initial first site charge: None
Modified first site charge to -1.0
```

## Storing and Loading

### Store in Database

```python
# Store the structure
structure.store()
print(f"Stored with PK: {structure.pk}")

# Load from database
loaded = orm.load_node(structure.pk)
print(f"Loaded: {loaded.properties.formula}")
```

**Output:**
```
Stored with PK: 13524
Loaded: Si2
```


## Key Takeaways

- ✅ **Easy Conversion**: Convert seamlessly from ASE Atoms objects using `StructureData.from_ase()`
- ✅ **Rich Properties**: Access comprehensive structural information through the `.properties` attribute:
    - Formula, cell volume, number of sites
    - Atomic positions, symbols, masses and more
    - Hubbard U and V
- ✅ **Site-Level Access**: Iterate through individual sites to access atomic positions and properties
- ✅ **Immutable vs. Mutable**:
    - `StructureData`: Immutable, AiiDA-compatible, database storage
    - `StructureDataMutable`: Mutable, for modifications, then convert back
- ✅ **Database Integration**: Store structures in AiiDA database with full provenance tracking
- ✅ **Property Discovery**: Use `get_supported_properties()` and `get_defined_properties()` to explore available data

## Next Steps

Now that you've learned the basics of creating and working with structures, here's what to explore next:

### ⚙️ **Running Calculations**
Use your structures in real computational workflows:
- **Tutorial**: [Running Your First QE Calculation](2_first_qe_calculation.md)
- **Topics**: Setting up calculations with aiida-quantumespresso, result analysis

---

**💡 Recommended Learning Path:**
1. ✅ **You are here** → Basic structure creation
3. ⚙️ **Next** → [First QE Calculation](2_first_qe_calculation.md)
2. 🧲 **Then** → [Magnetic Structures](magnetic_structures.md)
4. 📊 **Advanced** → [How-to Guides](../how_to/index.html)

Ready to your first calculation with the atomistic StructureData? Let's continue! 🚀
