### From Scratch

The most direct way is to define your structure using sites:

```python
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
        "kind_name": "H1",
    },
    {
        "symbol": "O",
        "position": np.array([1.5, 1.5, 1.5]),
        "kind_name": "O1",
    }
]

# Create the structure
structure = StructureData(cell=cell, pbc=pbc, sites=sites)
print(f"Created structure: {structure.properties.formula}")
```

### From pymatgen

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
```

**Output:**
```
Converted pymatgen structure: Si2
```


### From Files

Load structures from CIF files:

```python
# From CIF file
structure_from_file = StructureData.from_file('path/to/your/structure.cif')
```


### Export Formats

```python
# Export to ASE
ase_atoms = structure.to_ase()
print(f"Generated ASE atoms: {ase_atoms}\n")

# Export to pymatgen
pmg_struct = structure.to_pymatgen()
print(f"Generated pymatgen structure: {pmg_struct}")

# Export to file
structure.to_file('my_structure.cif')
```

**Output:**
```
Generated ASE atoms: Atoms(symbols='Si2', pbc=True, cell=[[3.84, 0.0, 2.3513218543629e-16], [1.92, 2.7152900397563, -1.92], [0.0, 0.0, 3.84]], masses=...)

Generated pymatgen structure: Full Formula (Si2)
Reduced Formula: Si
abc   :   3.840000   3.840000   3.840000
angles: 120.000000  90.000000  60.000000
pbc   :       True       True       True
Sites (2)
  #  SP       a    b     c
---  ----  ----  ---  ----
  0  Si    0     0    0
  1  Si    0.75  0.5  0.75
```
