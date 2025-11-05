# Immutability in StructureData

## Overview

In `aiida-atomistic`, there are two main structure classes with different mutability characteristics:

- **`StructureData`**: Immutable structure (used for AiiDA provenance tracking)
- **`StructureBuilder`**: Mutable structure (for construction and modification)

:::{important}
Once a `StructureData` object is created, **you cannot modify it**. This immutability is essential for maintaining data provenance in AiiDA workflows.
:::

## Why Immutability?

AiiDA's provenance graph requires that stored data nodes remain unchanged after creation. This ensures:

- **Reproducibility**: Workflow results remain consistent
- **Data integrity**: Historical data cannot be accidentally modified
- **Provenance tracking**: Clear input-output relationships in calculations

## Immutable vs Mutable: Key Differences

### StructureData (Immutable)

```python
from aiida_atomistic.data.structure import StructureData

# Create an immutable structure
structure = StructureData(**structure_dict)

# ❌ These operations will raise ValueError:
structure.properties.pbc[0] = False  # Cannot modify list elements
structure.properties.pbc = [True, False, True]  # Cannot reassign attributes
structure.properties.sites[0].symbol = "Fe"  # Sites are frozen
structure.set_cell([[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]])  # No setter methods
```

**Key characteristics:**
- All properties are read-only
- Lists are converted to `FrozenList` (immutable list subclass)
- Sites are `FrozenSite` objects
- No setter methods available
- Attempting to modify raises `ValueError`

### StructureBuilder (Mutable)

:::{important}
Why do we need a mutable version of the structure? While there are many materials science packages like ASE and Pymatgen that provide mutable structures, they often lack support for certain properties, such as Hubbard U and V parameters. To address this limitation, `StructureBuilder` offers a tailored solution, enabling the inclusion and modification of these additional properties, so we can define and modify them, and from there build up our `StructureData` instance.
:::

```python
from aiida_atomistic.data.structure import StructureBuilder

# Create a mutable structure
structure = StructureBuilder(**structure_dict)

# ✅ These operations work fine:
structure.set_pbc([True, False, True])  # Use setter methods
structure.set_cell([[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]])
structure.append_site(Site(symbol="Fe", position=[0, 0, 0], ...))
structure.update_sites(site_indices=0, charge=2.0)
```

**Key characteristics:**
- Properties can be modified using setter methods
- Sites are regular `Site` objects
- Setter methods available for all properties
- Direct manipulation possible (but use setters when available!)

## Working with Immutable Structures

### Creating Mutable Copies

If you need to modify an immutable structure, create a mutable copy:

```python
from aiida_atomistic.data.structure import StructureData, StructureBuilder

# Start with immutable structure
immutable = StructureData(**structure_dict)

# Create mutable copy
mutable = StructureBuilder(**immutable.to_dict())

# Modify the mutable copy
mutable.set_pbc([True, True, False])
mutable.append_site(Site(symbol="O", position=[1.0, 1.0, 1.0], ...))

# Convert back to immutable for storage
final_structure = StructureData(**mutable.to_dict())
```

### Using `get_value()` Method

```python
# Get a mutable copy directly
mutable_copy = immutable_structure.get_value()

# Modify and create new immutable structure
mutable_copy.set_cell([[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]])
new_immutable = StructureData(**mutable_copy.to_dict())
```

## Implementation Details

### Frozen Data Structures

The immutability is enforced through several mechanisms:

1. **Pydantic's `frozen=True` model config**: Prevents attribute reassignment
2. **`FrozenList` class**: Custom list subclass that raises `ValueError` on item assignment
3. **`FrozenSite` class**: Frozen version of `Site` model
4. **Custom `__setattr__` method**: Provides informative error messages

### FrozenList Behavior

```python
from aiida_atomistic.data.structure.site import FrozenList

# FrozenList is a list subclass
frozen = FrozenList([1, 2, 3])
print(frozen[0])  # ✅ Works: 1
len(frozen)  # ✅ Works: 3

# But modification raises ValueError
frozen[0] = 5  # ❌ Raises: ValueError
frozen.append(4)  # ❌ Raises: ValueError
```

## Best Practices

### ✅ DO:

- Use `StructureData` for AiiDA workflow inputs/outputs
- Build structures with `StructureBuilder`, then transform it into `StructureData`
- Use setter methods in mutable structures, to update a given property for all sites at once
- Use `to_dict()` for conversions between mutable/immutable

### ❌ DON'T:

- Try to modify `StructureData` properties directly

## Common Pitfalls

### Pitfall 1: Assuming Regular Lists

```python
# ❌ Wrong assumption
structure = StructureData(**structure_dict)
structure.properties.pbc[0] = False  # Looks like it should work, but raises ValueError

# ✅ Correct approach
mutable = StructureBuilder(**structure.to_dict())
mutable.set_pbc([False, True, True])
```

### Pitfall 2: Direct Property Manipulation in Mutable Structures

```python
# ⚠️ Risky (can cause inconsistencies)
mutable_structure.properties.sites.append(...)  # Bypasses validation

# ✅ Better (uses validation and keeps structure consistent)
mutable_structure.append_atom(Site(...))
```

## Error Messages

When attempting to modify immutable structures, you'll see:

```
ValueError: The AiiDA `StructureData` is immutable. You can create a mutable copy of it using its `get_value` method.
```

This message guides you to create a mutable copy when modifications are needed.
