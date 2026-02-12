# Hubbard Parameters

AiiDA-atomistic provides comprehensive support for Hubbard parameters in crystal structures, enabling proper modeling of strongly correlated materials with DFT+U and DFT+U+V methods. This functionality is particularly important for transition metal oxides, rare-earth compounds, and other materials with localized electrons.

## Overview

Hubbard parameters describe on-site and inter-site Coulomb interactions in materials with strongly correlated electrons. The implementation in `aiida-atomistic` supports:

- **On-site Hubbard U parameters** (e.g., U_eff, U, J)
- **Inter-site Hubbard V parameters** for neighbor interactions
- **Multiple formulations**: Dudarev (simplified) and Liechtenstein (full)
- **Various projectors**: atomic, ortho-atomic, norm-atomic, Wannier functions, pseudo-potentials
- **Flexible manifold definitions**: single orbital (e.g., `3d`) or orbital pairs (e.g., `3d-2p`)

:::{important}
**Hubbard Parameters Structure**

Each Hubbard parameter is defined by:
- **`atom_index`**: Index of the atom in the structure (0-based)
- **`atom_manifold`**: Orbital manifold (e.g., `'3d'`, `'3d-2p'`)
- **`neighbour_index`**: Index of the neighboring atom (same as atom_index for on-site)
- **`neighbour_manifold`**: Orbital manifold of the neighbor
- **`value`**: Parameter value in eV
- **`translation`**: Translation vector `[n1, n2, n3]` for periodic images
- **`hubbard_type`**: Type of parameter (`'Ueff'`, `'U'`, `'V'`, `'J'`, `'B'`, `'E2'`, `'E3'`)
:::

## Basic Usage

### Initializing On-Site Hubbard Parameters

The simplest way to add Hubbard parameters is using the `initialize_onsites_hubbard()` method:

```python
from aiida_atomistic.data.structure import StructureBuilder

# Create a structure
structure_dict = {
    'pbc': [True, True, True],
    'cell': [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]],
    'sites': [
        {
            'symbol': 'H',
            'position': [0.0, 0.0, 0.0],
            'mass': 1.008,
            'charge': 0.1,
            'kind_name': 'H1',
            'magmom': [0.0, 0.0, 2.2]
        },
        {
            'symbol': 'O',
            'position': [0.0, 0.0, 1.0],
            'mass': 15.999,
            'charge': -0.1
        }
    ]
}

structure = StructureBuilder(**structure_dict)

# Initialize on-site Hubbard U for all H atoms with kind 'H1'
structure.initialize_onsites_hubbard(
    atom_name='H1',      # Kind name or symbol
    atom_manifold='3d',  # Orbital manifold
    value=4.0,           # U value in eV
    hubbard_type='U',    # Type of parameter
    use_kinds=True       # Use kind names (not just symbols)
)

# Access the parameters
print(structure.properties.hubbard.parameters)
```

**Output:**
```
[HubbardParameters(atom_index=0, atom_manifold='3d', neighbour_index=0, neighbour_manifold='3d', translation=(0, 0, 0), value=4.0, hubbard_type='U')]
```

### Working with Multiple Kinds

When you have multiple kinds of the same element with different properties:

```python
# Initialize for specific kind
for kind in set(structure.properties.kind_names):
    if "H" in kind:
        structure.initialize_onsites_hubbard(
            atom_name=kind,
            atom_manifold='3d',
            value=4.0,
            hubbard_type='U',
            use_kinds=True
        )
```

### Initializing Inter-Site Hubbard Parameters

For inter-site V parameters between different atoms:

```python
# Initialize V parameters between Fe and O atoms
structure.initialize_intersites_hubbard(
    atom_name='Fe1',
    atom_manifold='3d',
    neighbour_name='O1',
    neighbour_manifold='2p',
    value=0.5,           # V value in eV
    hubbard_type='V',
    use_kinds=True
)
```

## Advanced Usage

### Manual Parameter Addition

For more control, you can manually append individual parameters:

```python
# Add a specific Hubbard parameter
structure.append_hubbard_parameter(
    atom_index=0,
    atom_manifold='3d',
    neighbour_index=0,
    neighbour_manifold='3d',
    value=4.0,
    translation=(0, 0, 0),  # No translation for on-site
    hubbard_type='Ueff'
)
```

### Working with Parameter Lists

You can work with parameters as lists of tuples:

```python
# Get parameters as list
params_list = structure.get_hubbard_list()
print(params_list)
# [(atom_index, atom_manifold, neighbour_index, neighbour_manifold,
#   value, translation, hubbard_type), ...]

# Set parameters from list
structure.set_hubbard_from_list(
    parameters=[
        (0, '3d', 0, '3d', 4.0, (0, 0, 0), 'Ueff'),
        (1, '2p', 1, '2p', 6.5, (0, 0, 0), 'Ueff'),
    ],
    projectors='ortho-atomic',
    formulation='dudarev'
)
```

### Managing Parameters

```python
# Remove the last parameter
structure.pop_hubbard_parameters()

# Remove a specific parameter by index
structure.pop_hubbard_parameters(index=0)

# Clear all parameters
structure.clear_hubbard_parameters()

# Remove all Hubbard data
structure.remove_hubbard()
```

### Accessing Hubbard Properties

```python
# Access the full Hubbard object
hubbard = structure.properties.hubbard

# Check the formulation and projectors
print(f"Formulation: {hubbard.formulation}")  # 'dudarev' or 'liechtenstein'
print(f"Projectors: {hubbard.projectors}")     # 'ortho-atomic', etc.

# Iterate over parameters
for param in hubbard.parameters:
    print(f"Atom {param.atom_index} ({param.atom_manifold}): "
          f"{param.hubbard_type} = {param.value} eV")
```
