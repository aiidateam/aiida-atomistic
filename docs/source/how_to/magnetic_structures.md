# Magnetic Structures

AiiDA-atomistic provides comprehensive support for magnetic properties in crystal structures. This enables modeling of magnetic materials with proper magnetic moment assignments and collinear/non-collinear magnetism support.

:::{important}
**Magnetic Properties: `magmom` vs `magnetization`**

`aiida-atomistic` provides two **mutually exclusive** site properties for magnetism:

- **`magmom`**: 3D vector `[x, y, z]` for non-collinear magnetism (e.g., `[0, 0, 2.2]`)
- **`magnetization`**: Scalar float for collinear magnetism along a fixed axis (e.g., `2.2`)

**Important:**
- You **cannot** set both `magmom` and `magnetization` on the same site
- Choose `magmom` for non-collinear spin structures
- Choose `magnetization` for collinear (spin-up/spin-down) calculations
- Additionally, you can define the total cell magnetization with `tot_magnetization`
:::

Here below a full example on how to set all possible magnetic properties:

```python
import numpy as np
from aiida_atomistic.data.structure import StructureBuilder

# Start with a basic iron structure
from ase.build import bulk
fe_atoms = bulk('Fe', 'bcc', a=2.87)

# Create mutable structure
structure = StructureBuilder.from_ase(fe_atoms)

# Add magnetic moments
print(f"Adding magnetic moments to {len(structure.sites)} site:")
for site in structure.sites:
    site.magmom = np.array([0.0, 0.0, 2.2])  # 2.2 µB along z-axis
# This can also be done via structure.set_magmoms([[0,0,2.2]]*len(structure.sites))
print(structure.properties.magmoms)

# Now remove magnetic moments and add magnetization
print(f"Removing magnetic moments from {len(structure.sites)} site and adding magnetization:")
structure.remove_magmoms()
structure.set_magnetizations([2.2])
print(structure.properties.magnetizations)

# Now remove magnetization as well and adding total magnetization
print(f"Removing magnetization and adding total magnetization:")
structure.remove_magnetizations()
structure.set_tot_magnetization(2.2)
print(structure.properties.tot_magnetization)
```

**Output:**
```
Adding magnetic moments to 1 site:
[[0.  0.  2.2]]
Removing magnetic moments from 1 site and adding magnetization:
[2.2]
Removing magnetization and adding total magnetization:
2.2
```
