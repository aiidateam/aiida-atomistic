# Creating and Modifying Structures

This guide shows you how to create and modify `StructureData` instances using different approaches.

:::{important}
`aiida-atomistic` provides two structure classes:
- **`StructureData`**: Immutable AiiDA `Data` node for provenance tracking (cannot be modified after creation, stored in database)
- **`StructureBuilder`**: Mutable Python helper class for building and editing structures before storing

**Key points:**
- `StructureBuilder` is purely a Python tool - not required to create `StructureData`
- You can create `StructureData` directly from dictionaries or other sources
- `StructureBuilder` is essentially the mutable counterpart of `StructureData`
- Properties can be set directly or via methods; full validation happens when creating the immutable `StructureData`
- For a complete list of definable properties, see the [in-depth page on properties](../in_depth/properties.md).

For more details on the immutability concept, please read the corresponding [in-depth page](../in_depth/immutability.md).
:::

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
        "position": np.array([0.0, 0.0, 0.0]),
        "mass": 1.008,
        "kind_name": "H1",
    },
    {
        "symbol": "O",
        "position": np.array([1.5, 1.5, 1.5]),
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
```
Created structure: HO
Number of sites: 2
```

### From Kinds-Based Dictionary

For structures with many repeated atoms, you can use a more compact kinds-based representation. This is especially useful for structures with many atoms sharing the same properties:

```python
from aiida_atomistic.data.structure import StructureData
import numpy as np

# Define structure using kinds (more compact for repeated atoms)
kinds_dict = {
    'cell': [[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]],
    'pbc': [True, True, True],
    'kinds': [
        {
            'symbol': 'Fe',
            'positions': [[0, 0, 0], [2, 2, 0]],  # Multiple positions
            'site_indices': [0, 1],
            'magmom': [0, 0, 2.2],
            'charge': 0.5,
        },
        {
            'symbol': 'O',
            'positions': [[1, 1, 0], [3, 3, 0]],
            'site_indices': [2, 3],
            'charge': -1.0,
        }
    ]
}

# Create structure from kinds dictionary
structure = StructureData.from_kinds_dict(kinds_dict)
print(f"Created structure: {structure.properties.formula}")
print(f"Number of sites: {len(structure.properties.sites)}")
print(f"Kinds: {set(structure.properties.kind_names)}")
```

**Output:**
```
Created structure: Fe2O2
Number of sites: 4
Kinds: {'Fe1', 'O1'}
```

**Advantages of kinds-based format:**
- More compact for structures with many equivalent atoms
- Explicit grouping of atoms with same properties
- Matches the internal storage format used by AiiDA
- Useful when migrating from legacy `orm.StructureData`

**When to use:**
- Structures with many atoms of the same type and properties
- Converting from legacy AiiDA format
- When you already have kind information from calculations
- Large structures where compactness matters

### From ASE

Convert ASE Atoms objects to StructureData:

```python
from ase.build import bulk

# Create ASE structure
ase_atoms = bulk('Cu', 'fcc', a=3.6)
print(f"ASE structure: {ase_atoms}")

# Convert to aiida-atomistic
structure = StructureData.from_ase(ase_atoms)
print(f"Converted structure: {structure.properties.formula}")
print(f"Cell volume: {structure.properties.cell_volume:.2f} Å³")
```

**Output:**
```
ASE structure: Atoms(symbols='Cu', pbc=True, cell=[0.0, 1.8, 1.8], [1.8, 0.0, 1.8], [1.8, 1.8, 0.0])
Converted structure: Cu
Cell volume: 11.66 Å³
```

#### With Magnetic Moments

ASE structures with magnetic moments are automatically converted to the magnetization (as they are just a float):

```python
from ase.build import bulk

# Create ASE structure with magnetic moments
atoms = bulk('Fe', 'bcc', a=2.87)
atoms.set_initial_magnetic_moments([2.2])

# Convert to aiida-atomistic
structure = StructureData.from_ase(atoms)
print(f"Magnetic moments: {structure.properties.magmoms}")
```

**Output:**
```
Magnetization: [2.2]
```

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
```
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
```
Converted pymatgen structure: Si2
Number of atoms: 2
```

#### With Site Properties

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
```
Charges: [2. 0.]
```

### From Files

Load structures from various file formats:

#### From CIF

```python
# From CIF file
structure = StructureData.from_file('path/to/your/structure.cif')
print(f"Loaded from CIF: {structure.properties.formula}")
```

#### From MCIF (Magnetic CIF)

Load magnetic structures from MCIF files:

```python
# From magnetic CIF file
structure = StructureData.from_file('examples/structure/data/Fe_bcc.mcif')

print(f"Loaded structure: {structure.properties.formula}")
print(f"Magnetic moments present: {structure.properties.magmoms is not None}")

# Check magnetic moments
if structure.properties.magmoms is not None:
    print(f"Magnetic moments:\n{structure.properties.magmoms}")
```

**Output:**
```
Loaded structure: Fe
Magnetic moments present: True
Magnetic moments:
[[0.  0.  2.5]]
```

### Backward compatibility: from Legacy orm.StructureData

It is possible to migrate from the old `orm.StructureData` to the new `aiida-atomistic` `StructureData`:

```python
from aiida.orm import StructureData as LegacyStructureData
from aiida_atomistic.data.structure.utils_orm import from_legacy_to_atomistic

legacy = LegacyStructureData(cell=[[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]])
legacy.append_atom(symbols='H', position=[0.0, 0.0, 0.0], mass=1.008, name='H1')
legacy.append_atom(symbols='O', position=[0.0, 0.0, 1.0], mass=15.999, name='O1')

s = from_legacy_to_atomistic(legacy_structure=legacy, metadata={'store_provenance': True}) # no need to define metadata, default is already True.
```

## Modifying Structures

:::{warning}
`StructureData` is **immutable** and cannot be modified. Use `StructureBuilder` for modifications.
:::

### Creating a Mutable Structure: the `StructureBuilder`

```python
from aiida_atomistic.data.structure import StructureBuilder

# Start with an empty mutable structure
mutable = StructureBuilder(
    cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    pbc=[True, True, True]
)

print(f"Initial structure has {len(mutable.properties.sites)} sites")
```

**Output:**
```
Initial structure has 0 sites
```

### Adding Sites

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
mutable.append_atom(site1)

# Add a site using dictionary
site2 = {
    "symbol": "O",
    "position": [1.5, 1.5, 1.5],
    "charge": -1.0,
    "kind_name": "O1"
}
mutable.append_atom(atom=site2)

print(f"Structure now has {len(mutable.properties.sites)} sites")
print(f"Formula: {mutable.properties.formula}")
```

**Output:**
```
Structure now has 2 sites
Formula: FeO
```

### Modifying Cell and PBC

```python
# Change cell
mutable.set_cell([[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]])
print(f"New cell volume: {mutable.properties.cell_volume:.2f} Å³")

# Change periodic boundary conditions
mutable.set_pbc([True, True, False])  # 2D slab
print(f"PBC: {mutable.properties.pbc}")
```

**Output:**
```
New cell volume: 64.00 Å³
PBC: [True, True, False]
```

### Modifying Site Properties

Update properties of existing sites:

```python
# Update a specific site's charge
mutable.update_sites(site_indices=0, charge=1.0)

# Update multiple sites
mutable.update_sites(site_indices=[0, 1], magmom=[[0, 0, 3.0], [0, 0, 0]])

print(f"Updated charges: {mutable.properties.charges}")
print(f"Updated magmoms:\n{mutable.properties.magmoms}")
```

**Output:**
```
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
mutable.set_charges([1.0, -1.0])

# Set magnetic moments for all sites (3D vectors)
mutable.set_magmoms([[0, 0, 2.5], [0, 0, 0]])

# OR set scalar magnetizations (mutually exclusive with magmoms!)
# mutable.set_magnetizations([2.5, 0])

print(f"Charges: {mutable.properties.charges}")
```

:::{warning}
**Magnetic Properties are Mutually Exclusive:**
- `magmom` (3D vector) and `magnetization` (scalar) cannot both be set on the same site
- Use `magmom` for non-collinear magnetism: `[x, y, z]`
- Use `magnetization` for collinear magnetism: scalar value
- See the [Magnetic Structures guide](magnetic_structures.md) for details
:::

### Removing Properties

To remove properties from a mutable structure:

```python
# Remove charges from all sites
mutable.remove_charges()
print(f"Charges after removal: {mutable.properties.charges}")  # None

# Remove magnetic moments
mutable.remove_magmoms()
print(f"Magmoms after removal: {mutable.properties.magmoms}")  # None
```

:::{note}
**Setting vs. Validation:**
- In `StructureBuilder`, you can set properties directly (e.g., `mutable.properties.sites[0].charge = 2.0`) or use setter methods (e.g., `mutable.set_charges([2.0, -1.0])`)
- Full validation occurs only when converting to `StructureData` (the immutable version)
- This allows you to build structures incrementally without premature validation errors
- See the full list of properties in the [Site API documentation](../reference/api/auto/aiida_atomistic/data/structure/site/index.rst)
:::

## Conversion Between `StructureBuilder` and `StructureData` (and viceversa)

The `StructureBuilder` object is a pure python class, any instance of it needs to be converted into the `StructureData` before being used in an AiiDA process.
It is possible to seamlessly convert between `StructureBuilder` and `StructureData` (and viceversa) using the defined `to_*` and `from_*` methods:

```python
# StructureBuilder → StructureData (for storage in AiiDA)
structuredata = structurebuilder.to_aiida()
structuredata = StructureData.from_builder(structurebuilder)

# Immutable → Mutable (for editing)
structurebuilder = structuredata.to_builder()
structurebuilder = StructureBuilder.from_aiida(structuredata)

```

## Generating Kinds Automatically

Automatically detect and assign kind names based on site properties:

```python
# Create structure without kind names
mutable = StructureBuilder(
    cell=[[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]],
    pbc=[True, True, True],
    sites=[
        {"symbol": "Fe", "position": [0, 0, 0], "magmom": [0, 0, 2.2]},
        {"symbol": "Fe", "position": [2.5, 0, 0], "magmom": [0, 0, 2.2]},
        {"symbol": "Fe", "position": [0, 2.5, 0], "magmom": [0, 0, -2.2]},
    ]
)

# Generate kinds based on properties
mutable = mutable.to_kinds_based()

print(f"Generated kinds: {set(mutable.properties.kind_names)}")
```

For more details, see the [Kinds documentation](../in_depth/kinds.md).

## Export Formats

### Export to ASE

```python
# Export to ASE
ase_atoms = structure.to_ase()
print(f"ASE atoms: {ase_atoms}")
print(f"Cell: {ase_atoms.cell}")
```

**Output:**
```
ASE atoms: Atoms(symbols='Si2', pbc=True, ...)
Cell: Cell([[1.42015, 1.42015, 1.42015], ...]
```

### Export to pymatgen

```python
# Export to pymatgen
pmg_struct = structure.to_pymatgen()
print(f"Pymatgen structure:\n{pmg_struct}")
```

**Output:**
```
Pymatgen structure:
Full Formula (Fe1)
Reduced Formula: Fe
abc   :   2.459772   2.459772   2.459772
angles: 109.471221 109.471221 109.471221
pbc   :       True       True       True
Sites (1)
  #  SP      a    b    c  magmom
---  ----  ---  ---  ---  -------------
  0  Fe      0    0    0  [0.  0.  2.5]
```

### Export to Files

```python
# Export to CIF
structure.to_file('my_structure.cif')

# Export to other formats supported by ASE
structure.to_file('my_structure.xyz')
```

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
builder = builder.to_kinds_based(tolerance={'magmom': 1e-2, 'charge': 1e-3})

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
```
Structure: Fe2O2
Kinds: {'Fe1', 'O1', 'Fe2'}
Cell volume: 125.00 Å³

Final structure ready for calculations!
Is alloy: False
Total charge: -1.0
```

## Best Practices

### ✅ DO:

- Use `StructureBuilder` for building and editing structures
- Convert to `StructureData` when ready to store or use in calculations
- Use `generate_kinds()` to automatically detect equivalent atoms
- Set `kind_name` explicitly when you have specific requirements (e.g., symmetry)
- Use appropriate tolerances for kind generation based on your property accuracy

### ❌ DON'T:

- Try to modify `StructureData` properties directly (it will raise an error)

## Common Patterns

### Pattern 1: Load, Modify, Store

```python
# Load existing structure
original = StructureData.from_file('structure.cif')

# Create mutable copy
mutable = StructureBuilder(**original.to_dict())

# Modify
mutable.set_charges([1.0] * len(mutable.properties.sites))
mutable = mutable.to_kinds_based(kinds)

# Store
modified = StructureData(**mutable.to_dict())
```

### Pattern 2: Build from Scratch

```python
# Start empty
builder = StructureBuilder(cell=cell, pbc=pbc)

# Add atoms iteratively
for position, element in zip(positions, elements):
    builder.append_atom(atom={"symbol": element, "position": position})

# Finalize
structure = StructureData(**builder.to_dict())
```

### Pattern 3: Convert and Enhance

```python
# Import from external format
from ase.build import bulk
ase_structure = bulk('Fe', 'bcc', a=2.87)

# Convert
structure = StructureData.from_ase(ase_structure)

# Enhance with additional properties
mutable = StructureBuilder(**structure.to_dict())
mutable.set_magmoms([[0, 0, 2.2]])

# Finalize
enhanced = StructureData(**mutable.to_dict())
```

## See Also

- [Immutability Guide](../in_depth/immutability.md) - Deep dive into mutable vs immutable
- [Magnetic Structures](magnetic_structures.md) - Working with magnetic moments
- [Kinds Documentation](../in_depth/kinds.md) - Understanding the kinds system
- [Adding Properties](add_properties.md) - Extending with custom properties
