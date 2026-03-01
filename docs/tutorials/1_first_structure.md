# Creating Your First Structure

In this short tutorial you will learn how to create your first structure, inspect its properties and how to store it in the AiiDA database to then use it in your calculations.

!!! note
    `aiida-atomistic` provides two structure classes:

    - **`StructureData`**: Immutable structure for AiiDA provenance (cannot be modified after creation)
    - **`StructureBuilder`**: Mutable structure for building and editing, before creating the `StructureData` from it

    for more details, please read the [in-depth page on immutability](../in_depth/immutability.md).


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
```text
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
```text
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
```text
Site 0: Si at [0. 0. 0.]
Site 1: Si at [1.3575 1.3575 1.3575]
```

Information on the supported and defined properties can be obtained by using the `get_supported_properties` and `get_defined_properties` methods.

## Discovering Properties at Runtime

Four class/instance methods let you inspect the property system without reading the source code:

| Method | Called on | Returns | Use when you want to know… |
|---|---|---|---|
| `get_supported_properties()` | class | `dict` with keys `'global'` and `'site'` | What properties *can* be set at all |
| `get_computed_properties()` | class | `set` of names | Which properties are *derived* (never set by the user) |
| `get_defined_properties()` | instance | `set` of names | Which properties are *actually set* on this structure |
| `get_queryable_properties()` | class | `dict` with keys `'queryable'` / `'not_queryable'` | Which properties can be filtered with `QueryBuilder` |

```python
from aiida_atomistic.data import StructureData

# --- 1. What can be set? ---
supported = StructureData.get_supported_properties()
print("Global fields :", supported['global'])
# → {'pbc', 'cell', 'sites', 'tot_charge', 'tot_magnetization', 'hubbard', 'custom'}
print("Site fields   :", supported['site'])
# → {'symbol', 'position', 'mass', 'charge', 'magmom', 'magnetization', 'weight', 'kind_name', ...}

# --- 2. Which are computed (never user-set)? ---
computed = StructureData.get_computed_properties()
print("Computed      :", computed)
# → {'formula', 'cell_volume', 'dimensionality', 'is_alloy', 'has_vacancies',
#    'composition', 'n_sites', 'n_kinds', 'positions', 'symbols', 'masses',
#    'charges', 'magmoms', 'magnetizations', 'weights', 'kind_names', 'kinds',
#    'max_charge', 'min_charge', 'max_magmom', 'min_magmom',
#    'max_magnetization', 'min_magnetization'}

# --- 3. What is set on *this* structure? ---
structure = StructureData.from_ase(ase_atoms)
defined = structure.get_defined_properties()
print("Defined       :", defined)
# → {'cell', 'pbc', 'sites', 'positions', 'symbols', 'masses'}
#   (only user-set fields + site arrays; pure computed like formula excluded by default)

# Pass exclude_computed_without_singular=False to also see formula, cell_volume, etc.
defined_all = structure.get_defined_properties(exclude_computed_without_singular=False)

# --- 4. What can be queried in the database? ---
queryable = StructureData.get_queryable_properties()
print("Queryable     :", queryable['queryable'])
# → ['cell', 'cell_volume', 'composition', 'dimensionality', 'has_vacancies',
#    'is_alloy', 'max_charge', 'min_charge', 'n_sites', 'pbc', 'symbols', ...]
print("Not queryable :", queryable['not_queryable'])
# → ['charges', 'magmoms', 'masses', 'positions', 'weights', ...]  (stored in files)
```

!!! tip
    `get_defined_properties()` is especially useful before passing a structure to a plugin —
    call `check_plugin_unsupported_props(structure, plugin_supported_properties)` to see
    which properties the plugin cannot handle.
    See the [Plugin Migration guide](../dev_guides/dev_plugin_migration.md) for details.

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
```text
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
```text
Created mutable structure with 2 sites
Initial first site charge: None
Modified first site charge to -1.0
```
