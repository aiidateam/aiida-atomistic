# Creating and Modifying Structures

This guide shows you how to create and modify `StructureData` instances using different approaches.

???+ warning
    The `aiida-atomistic` package provides two structure classes:

    - **`StructureData`**: Immutable AiiDA `Data` node stored in the database for provenance tracking
    - **`StructureBuilder`**: Mutable Python class for building and editing structures before storing them as AiiDA nodes

    **Key points:**

    - `StructureBuilder` is purely a Python tool - not required to create `StructureData`
    - You can create `StructureData` directly from dictionaries or other sources (as explained in the following)
    - `StructureBuilder` is essentially the mutable counterpart of `StructureData`, but implementing also `setter` methods
    - Properties can be set directly or via methods; full validation happens when creating the immutable `StructureData`


## Creating Structures

### From Scratch

The most direct way is to define your structure using sites:

```python
from aiida_atomistic.data.structure import StructureData
import numpy as np

# Define unit cell (3x3x3 Å cubic cell)
cell = np.array([
    [3.0, 0.0, 0.0],
    [0.0, 3.0, 0.0],
    [0.0, 0.0, 3.0]
])

# Define periodic boundary conditions
pbc = [True, True, True]

# Define sites with properties
sites = [
    {
        "symbol": "H",
        "position": [0.0, 0.0, 0.0],
        "mass": 1.008,
        "kind_name": "H1",
    },
    {
        "symbol": "O",
        "position": [1.5, 1.5, 1.5],
        "mass": 15.999,
        "kind_name": "O1",
    }
]

# Create the structure
structure = StructureData(cell=cell, pbc=pbc, sites=sites)
print(f"Created structure: {structure.properties.formula}")
print(f"Number of sites: {len(structure.properties.sites)}")
```

**Output:**
```text
Created structure: HO
Number of sites: 2
```

???+ note
    Some of the most common properties like sites, cell, pbc, kinds, formula (and so on) are directly accessible as attributes of the object, without passing throught the `properties` attribute. For example, you can access sites via `structure.sites`.

#### Alloys and vacancies

To create an alloy, you can provide a list of elements as site symbol, and corresponding weights:

```python
sites = [
    {
        "symbol": ["Cu", "Zn"],
        "position": [0.0, 0.0, 0.0],
        "mass": 1.008,
        "weight": (0.6, 0.4)
    }
]
```

For a vacancy, the site should have one element, but a weight lower than 1:

```python
sites = [
    {
        "symbol": "Cu",
        "position": [0.0, 0.0, 0.0],
        "mass": 1.008,
        "weight": (0.6,)
    }
]
```

### From ASE

Convert ASE Atoms objects to StructureData:

```python
from ase.build import bulk

# Create ASE structure
ase_atoms = bulk('Cu', 'fcc', a=3.6)
print(f"ASE structure: {ase_atoms}")
print(f"ASE tags: {ase_atoms.get_tags()}")

# Convert to aiida-atomistic
structure = StructureData.from_ase(ase_atoms)
print(f"Converted structure: {structure.properties.formula}")
print(f"Cell volume: {structure.properties.cell_volume:.2f} Å³")
print(f"StructureData kinds: {structure.properties.kinds}")
```

**Output:**
```text
ASE structure: Atoms(symbols='Cu', pbc=True, cell=[[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0]])
ASE tags: [0]
Converted structure: Cu
Cell volume: 11.66 Å³
StructureData kinds: None
```

???+ warning
    If no Atoms tags are defined or are all the same, they will be ignored by the `from_ase`: kinds will not be assigned to the structure. To update a posteriori and define kinds, you can use the `StructureBuilder` (as shown later in this page).


#### Introducing magnetism in the structure

ASE structures with magnetic moments are automatically converted to the magnetization (as they are just a float):

```python
from ase.build import bulk

# Create ASE structure and assign float magnetic moments
atoms = bulk('Fe', 'bcc', a=2.87)
atoms.set_initial_magnetic_moments([2.2])

# Convert to aiida-atomistic
structure = StructureData.from_ase(atoms)
print(f"Magnetization: {structure.properties.magnetizations}")
```

**Output:**
```text
Magnetization: [2.2]
```

For more details on the definition of magnetic properties please refer to the [Magnetic Structures](magnetic_structures.md) page.

#### With Charges

```python
from ase.build import bulk

# Create ASE structure with charges
atoms = bulk('Cu', 'fcc', a=3.6)
atoms.set_initial_charges([1.0])

# Convert to aiida-atomistic
structure = StructureData.from_ase(atoms)
print(f"Charges: {structure.properties.charges}")
```

**Output:**
```text
Charges: [1.]
```

### From pymatgen

Convert pymatgen Structure objects:

```python
from pymatgen.core import Lattice, Structure

# Create pymatgen structure
coords = [[0, 0, 0], [0.75, 0.5, 0.75]]
lattice = Lattice.from_parameters(a=3.84, b=3.84, c=3.84, alpha=120,
                                beta=90, gamma=60)
pmg_struct = Structure(lattice, ["Si", "Si"], coords)

# Convert to aiida-atomistic
structure = StructureData.from_pymatgen(pmg_struct)
print(f"Converted pymatgen structure: {structure.properties.formula}")
print(f"Number of atoms: {len(structure.properties.sites)}")
```

**Output:**
```text
Converted pymatgen structure: Si2
Number of atoms: 2
```

#### Adding Site Properties

Pymatgen site properties are preserved:

```python
from pymatgen.core import Lattice, Structure

# Create structure with site properties
coords = [[0, 0, 0], [0.5, 0.5, 0.5]]
lattice = Lattice.cubic(4.0)
pmg_struct = Structure(lattice, ["Fe", "O"], coords)

# Add charge to first site
pmg_struct.sites[0].properties["charge"] = 2.0

# Convert
structure = StructureData.from_pymatgen(pmg_struct)
print(f"Charges: {structure.properties.charges}")
```

**Output:**
```text
Charges: [2. 0.]
```

### From Files

Load structures from various file formats, via the `from_file` method. It is possible to specify the parser engine between "ase" and "pymatgen".If the file is not a .cif or .mcif, the default is ase. To change it, you can pass the `parser="pymatgen"` input parameters to the method.

#### From CIF

```python
# From CIF file ()
structure = StructureData.from_file('aiida-atomistic/examples/structure/data/Ge.cif') # this is from examples contained in aiida-atomistic
print(f"Loaded from CIF: {structure.properties.formula}")
```

**Output:**
```text
Loaded from CIF: Ge2
```

#### From MCIF (Magnetic CIF)

Load magnetic structures from MCIF files:

```python
# From magnetic CIF file
structure = StructureData.from_file('aiida-atomistic/examples/structure/data/Fe_bcc.mcif')

print(f"Loaded structure: {structure.properties.formula}")
print(f"Magnetic moments present: {structure.properties.magmoms is not None}")

# Check magnetic moments
if structure.properties.magmoms is not None:
    print(f"Magnetic moments:\n{structure.properties.magmoms}")
```

**Output:**
```text
Loaded structure: Fe2
Magnetic moments present: True
Magnetic moments:
[[0.  0.  2.5]
 [0.  0.  2.5]]
```

### Backward compatibility: from Legacy orm.StructureData

It is possible to migrate from the old `orm.StructureData` to the new `aiida-atomistic` `StructureData`:

```python
from aiida.orm import StructureData as LegacyStructureData
from aiida_atomistic.data.structure.utils_orm import from_legacy_to_atomistic

legacy = LegacyStructureData(cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]])
legacy.append_atom(symbols='H', position=[0.0, 0.0, 0.0], mass=1.008, name='H1')
legacy.append_atom(symbols='O', position=[0.0, 0.0, 1.0], mass=15.999, name='O1')

structure = legacy.to_atomistic()
```

## Modifying Structures

!!! warning "Immutability"
    `StructureData` is **immutable** and cannot be modified. Attempting to modify `StructureData` properties directly will raise an error.
    Use `StructureBuilder` for modifications.


### Creating a Mutable Structure: the `StructureBuilder`

```python
from aiida_atomistic.data.structure import StructureBuilder

# Start with an empty mutable structure
builder = StructureBuilder(
    cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    pbc=[True, True, True]
)

print(f"Initial structure has {len(builder.properties.sites)} sites")
```

**Output:**
```text
Initial structure has 0 sites
```

### Adding Sites to the structure

Use `append_atom()` to add atoms:

```python
from aiida_atomistic.data.structure.site import Site

# Add a site using Site object
site1 = Site(
    symbol="Fe",
    position=[0, 0, 0],
    magmom=[0, 0, 2.2],
    charge=0.5,
    kind_name="Fe1"
)
builder.append_atom(site1)

# Add a site using dictionary
site2 = {
    "symbol": "O",
    "position": [1.5, 1.5, 1.5],
    "charge": -1.0,
    "kind_name": "O1"
}
builder.append_atom(atom=site2)

print(f"Structure now has {len(builder.properties.sites)} sites")
print(f"Formula: {builder.properties.formula}")
```

**Output:**
```text
Structure now has 2 sites
Formula: FeO
```

### Modifying Cell and PBC

```python
# Change cell
builder.set_cell([[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]])
print(f"New cell volume: {builder.properties.cell_volume:.2f} Å³")

# Change periodic boundary conditions
builder.set_pbc([True, True, False])  # 2D slab
print(f"PBC: {builder.properties.pbc}")
```

**Output:**
```text
New cell volume: 64.00 Å³
PBC: [True, True, False]
```

### Modifying properties of a specific site

Update properties of existing sites:

```python
# Update a specific site's charge
builder.update_sites(site_indices=0, charge=1.0)
# alternatively: builder.properties.sites[0].charge = 1.0

# Update multiple sites
builder.update_sites(site_indices=[0, 1], magmom=[[0, 0, 3.0], [0, 0, 0]])

print(f"Updated charges: {builder.properties.charges}")
print(f"Updated magmoms:\n{builder.properties.magmoms}")
```

**Output:**
```text
Updated charges: [ 1. -1.]
Updated magmoms:
[[[0. 0. 3.]
  [0. 0. 0.]]

 [[0. 0. 3.]
  [0. 0. 0.]]]
```

### Setting Properties for All Sites

```python
# Set charges for all sites
builder.set_charges([1.0, -1.0])

# Set magnetic moments for all sites (3D vectors)
builder.set_magmoms([[0, 0, 2.5], [0, 0, 0]])

# OR set scalar magnetizations (mutually exclusive with magmoms!)
# builder.set_magnetizations([2.5, 0])
```

!!! note ""
    **Magnetic Properties are Mutually Exclusive:**

    - `magmom` (3D vector) and `magnetization` (scalar) cannot both be set on the same site
    - Use `magmom` for non-collinear magnetism: `[x, y, z]`
    - Use `magnetization` for collinear magnetism: scalar value
    - See the [Magnetic Structures guide](magnetic_structures.md) for more details

### Removing Properties

To remove properties from a mutable structure:

```python
# Remove charges from all sites
builder.remove_charges()
print(f"Charges after removal: {builder.properties.charges}")  # None

# Remove magnetic moments
builder.remove_magmoms()
print(f"Magmoms after removal: {builder.properties.magmoms}")  # None
```

**Output**
```
Charges after removal: None
Magmoms after removal: None
```

???+ note
    **Setting vs. Validation:**

    - In `StructureBuilder`, you can set properties directly (e.g., `builder.properties.sites[0].charge = 2.0`) or use setter methods (e.g., `builder.set_charges([2.0, -1.0])`)
    - Full validation occurs only when converting to `StructureData` (the immutable version)
    - This allows you to build structures incrementally without premature validation errors

## Conversion Between `StructureBuilder` and `StructureData` (and viceversa)

The `StructureBuilder` object is a pure python class, any instance of it needs to be converted into the `StructureData` before being used in an AiiDA process.
It is possible to seamlessly convert between `StructureBuilder` and `StructureData` (and viceversa) using the defined `to_*` and `from_*` methods:

```python
# StructureBuilder → StructureData (for storage in AiiDA)
structuredata = builder.to_aiida()
structuredata = StructureData.from_builder(builder)

# Immutable → Mutable (for editing)
structurebuilder = structuredata.to_builder()
structurebuilder = StructureBuilder.from_aiida(structuredata)

```

## Generating Kinds Automatically

Once initialised our `StructureBuilder` (or `StructureData`), it is possible to automatically detect the kinds, based on the defined properties.
This can be achieved by using the `to_kinds` method, which returns, as output, a **new** instance with the assigned kind names:

```python
# Create structure without kind names
builder = StructureBuilder(
    cell=[[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]],
    pbc=[True, True, True],
    sites=[
        {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
        {"symbol": "Fe", "position": [2.5, 0, 0], "magmom": [0, 0, 2.2]},
        {"symbol": "Fe", "position": [0, 2.5, 0], "magmom": [0, 0, -2.2]},
    ]
)

# Generate kinds based on properties
builder_kinds = builder.to_kinds()

print(f"Generated kinds: {set(builder_kinds.properties.kind_names)}")

for kind in builder_kinds.kinds:
    print(f"Kind: {kind.name}, Symbol: {kind.symbol}, Mass: {kind.mass}, Magmom: {kind.magmom}, sites: {kind.site_indices}")
```

Kinds are also directly accessible via `builder_kinds.kinds`. For more details, see the [Kinds documentation](../in_depth/kinds.md).

## Export Formats

### Export to ASE

```python
# Export to ASE
ase_atoms = structure.to_ase()
print(f"ASE atoms: {ase_atoms}")
print(f"Cell: {ase_atoms.cell}")
```

**Output:**
```text
ASE atoms: Atoms(symbols='Fe2', pbc=True, ...
Cell: Cell([[2.8403, 0.0, 1.7391821518091137e-16], ...
```

### Export to pymatgen

```python
# Export to pymatgen
pmg_struct = structure.to_pymatgen()
print(f"Pymatgen structure:\n{pmg_struct}")
```

**Output:**
```text
Pymatgen structure:
Full Formula (Fe2)
Reduced Formula: Fe
abc   :   2.840300   2.840300   2.840300
angles:  90.000000  90.000000  90.000000
pbc   :       True       True       True
Sites (2)
  #  SP      a    b    c  magmom
---  ----  ---  ---  ---  -------------
  0  Fe    0    0    0    [0.  0.  2.5]
  1  Fe    0.5  0.5  0.5  [0.  0.  2.5]
```

### Export to Files

```python
# Export to CIF
structure.to_file('my_structure.cif')

# Export to other formats supported by ASE
structure.to_file('my_structure.xyz')
```

## Slicing structures

Both `StructureData` and `StructureBuilder` support Python-style indexing to
extract a subset of sites into a new structure.

???+ note
    The return type depends on the class you slice:

    - **`StructureBuilder[…]`** → a new `StructureBuilder` (mutable, can be edited
    further before storing).
    - **`StructureData[…]`** → a new, **unstored** `StructureData` node. Call
    `.store()` when you are ready to persist the result.


All global properties — `cell`, `pbc`, `tot_charge`, `tot_magnetization`,
`custom`, etc. — are **preserved** in the result unchanged.  Derived per-site
quantities such as `formula` and `n_sites` are recomputed automatically from the
new site list.

### Supported index types

| Index type | Example | Description |
| --- | --- | --- |
| `int` | `s[0]`, `s[-1]` | Single site (negative indices supported) |
| `slice` | `s[10:20]`, `s[::2]` | Contiguous or strided range |
| `list` / `tuple` of ints | `s[[0, 5, 12]]` | Arbitrary, possibly non-contiguous selection |
| 1-D numpy integer array | `s[np.array([0, 5, 12])]` | Same as list |

### Examples

```python
from aiida_atomistic.data.structure import StructureData, StructureBuilder
import numpy as np

# --- build a small 6-site structure ---
sites = [
    {"symbol": "Fe", "position": [0.0, 0.0, float(i)], "charge": float(i)}
    for i in range(6)
]
builder = StructureBuilder(
    cell=np.eye(3) * 10.0,
    pbc=[True, True, True],
    sites=sites,
)

# int — one site
one = builder[0]
print(one.properties.formula)   # Fe

# slice — first three sites
first3 = builder[0:3]
print(first3.properties.formula)  # Fe3

# slice with stride — every other site
even = builder[::2]
print(len(even))  # 3

# list — arbitrary selection
subset = builder[[0, 2, 5]]
print(subset.properties.formula)  # Fe3

# negative index
last = builder[-1]
print(last.properties.sites[0].position)  # [0. 0. 5.]
```

### Slicing a stored `StructureData` node

`StructureData` supports exactly the same indexing syntax and returns a new,
**unstored** `StructureData` node each time.  The original node is never modified.

```python
# Assume `node` is a stored StructureData retrieved from the database
node = load_node(pk=42)

# Extract the first 100 sites and store as a new node
sub = node[0:100]
sub.store()

# Arbitrary selection from a mask
mask = np.where(np.array(node.properties.charges) > 0.5)[0]
charged = node[mask]
charged.store()
```

!!! note ""
    `len(node)` and `len(builder)` return the number of sites, consistent with the indexing behaviour.

## Complete Example: Building a Complex Structure

Here's a complete workflow showing structure creation and modification:

```python
from aiida_atomistic.data.structure import StructureData, StructureBuilder
from aiida_atomistic.data.structure.site import Site
import numpy as np

# 1. Create mutable structure
builder = StructureBuilder(
    cell=np.eye(3) * 5.0,
    pbc=[True, True, True]
)

# 2. Add atoms with different properties
sites_to_add = [
    {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.5], "charge": 0.5},
    {"symbol": "Fe", "position": [2.5, 2.5, 0], "magmom": [0, 0, -2.5], "charge": 0.5},
    {"symbol": "O", "position": [1.25, 1.25, 0], "charge": -1.0},
    {"symbol": "O", "position": [3.75, 3.75, 0], "charge": -1.0},
]

for site in sites_to_add:
    builder.append_atom(atom=site)

# 3. Generate kinds automatically
builder = builder.to_kinds(threshold={'magmom': 1e-2, 'charge': 1e-3})

print(f"Structure: {builder.properties.formula}")
print(f"Kinds: {set(builder.properties.kind_names)}")
print(f"Cell volume: {builder.properties.cell_volume:.2f} Å³")

# 4. Convert to immutable for storage
final_structure = StructureData(**builder.to_dict())

# 5. Store in AiiDA (if needed)
# final_structure.store()

print(f"\nFinal structure ready for calculations!")
print(f"Is alloy: {final_structure.properties.is_alloy}")
print(f"Total charge: {np.sum(final_structure.properties.charges)}")
```

**Output:**

```text
Structure: Fe2O2
Kinds: {'Fe1', 'Fe2', 'O1'}
Cell volume: 125.00 Å³

Final structure ready for calculations!
Is alloy: False
Total charge: -1.0
```
