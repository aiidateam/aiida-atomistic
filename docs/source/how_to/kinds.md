# Kinds and Automatic Kind Generation

In crystallography and materials science, **kinds** represent groups of atoms that share the same chemical and physical properties. Atoms of the same kind have:

- Same chemical symbol
- Same mass
- Same charge
- Same magnetic moment (magnitude and direction)
- Same other properties

Kinds are particularly useful for:
- **Reducing data redundancy**: Store properties once per kind instead of per atom
- **Grouping equivalent atoms**: Identify symmetry-equivalent positions
- **Optimizing storage**: Compress structure data in the database
- **Plugin compatibility**: Some simulation codes use kind-based representations

## Manual Kind Assignment

You can manually assign kind names when creating a structure:

```python
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]],
    "sites": [
        {
            "symbol": "Fe",
            "position": [0.0, 0.0, 0.0],
            "magmom": [0.0, 0.0, 2.2],
            "kind_name": "Fe1",  # Manually assigned
        },
        {
            "symbol": "Fe",
            "position": [2.5, 2.5, 2.5],
            "magmom": [0.0, 0.0, -2.2],
            "kind_name": "Fe2",  # Different kind due to opposite spin
        },
    ],
}

structure = StructureData(**structure_dict)
print(structure.properties.kind_names)  # ['Fe1', 'Fe2']
```

## Automatic Kind Generation

The `generate_kinds()` method automatically detects and assigns kinds based on site properties:

```python
from aiida_atomistic.data.structure import StructureBuilder

structure_dict = {
    "pbc": [True, True, True],
    "cell": [[5.0, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 5.0]],
    "sites": [
        {
            "symbol": "Fe",
            "position": [0.0, 0.0, 0.0],
            "magmom": [0.0, 0.0, 2.2],
        },
        {
            "symbol": "Fe",
            "position": [2.5, 2.5, 2.5],
            "magmom": [0.0, 0.0, -2.2],
        },
    ],
}

structure = StructureBuilder(**structure_dict)

# Generate kinds automatically
structure = structure.to_kinds_based()

# Access the generated kinds
print(structure.properties.kinds)
```

### How It Works

The algorithm groups sites by comparing all their properties:

1. **Compares properties**: symbol, mass, charge, magmom, magnetization, weight
2. **Groups similar sites**: Sites within tolerance are assigned the same kind
3. **Generates kind names**: Unique names like "Fe1", "Fe2", "O1", etc.
4. **Updates sites**: Each site gets its `kind_name` assigned

## Tolerance System

Tolerances control how strictly properties must match for sites to be considered the same kind.

### Default Tolerances

Each property in the `Site` model has a default tolerance value stored in its field metadata. You can access these default tolerances programmatically:

```python
from aiida_atomistic.data.structure import Site

# Get all default tolerances
default_tolerances = Site.get_default_tolerances()
print(default_tolerances)
# {'mass': 0.001, 'charge': 0.01, 'magmom': 0.01, 'magnetization': 0.01, 'weight': 0.01}
```

When you call `generate_kinds()` without specifying tolerances, these property-specific defaults are used automatically.

### Custom Global Tolerance

You can override the defaults by specifying a single tolerance for all properties:

```python
# More strict: require exact matches for all properties
structure.generate_kinds(tolerance=1e-6)

# More relaxed: allow larger differences for all properties
structure.generate_kinds(tolerance=1e-2)
```

:::{note}
When you provide a single float value for `tolerance`, it overrides **all** the property-specific defaults.
:::

### Property-Specific Tolerances

You can selectively override individual property tolerances while keeping the defaults for others:

```python
# Override only specific properties
tolerances = {
    "magmom": 1e-1,      # More relaxed magnetic moment tolerance
    "charge": 1e-5,      # Stricter charge tolerance than default
    # mass, position, etc. will use their default values
}

structure.generate_kinds(tolerance=tolerances)
```

This approach gives you fine-grained control while maintaining sensible defaults for properties you don't specify.

:::{note}
Available tolerance keys can be inspected using the `Site.get_default_tolerances()` method.
:::

### Tolerance Behavior

The tolerance system uses **rounding-based comparison**:

```python
# For a property value v and tolerance tol:
normalized_value = round(v / tol) * tol

# Two values are "equal" if their normalized values match
```

**Example:**
```python
# With tolerance = 1e-2 (0.01)
magmom1 = [0.0, 0.0, 2.201]
magmom2 = [0.0, 0.0, 2.209]

# Both round to [0.0, 0.0, 2.21] → Same kind

magmom3 = [0.0, 0.0, 2.215]
# Rounds to [0.0, 0.0, 2.22] → Different kind
```

## Kinds Validation

### Automatic Validation

By default, `StructureData` validates kinds on creation:

```python
# This validates that sites with the same kind_name have identical properties
structure = StructureData(**structure_dict, validate_kinds=True)  # Default is False
```

If validation fails, you'll get an error:

```python
# These two sites have the same kind_name but different charges → Error!
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "sites": [
        {"symbol": "Cu", "position": [0, 0, 0], "charge": 1.0, "kind_name": "Cu1"},
        {"symbol": "Cu", "position": [1.5, 1.5, 1.5], "charge": 2.0, "kind_name": "Cu1"},  # ❌ Different charge!
    ],
}

structure = StructureData(**structure_dict)  # Raises ValidationError
```

### Manual Validation

For mutable structures, validate kinds explicitly:

```python
structure = StructureBuilder(**structure_dict)

# Validate the current kind assignments
try:
    structure.validate_kinds()
    print("Kinds are valid!")
except ValueError as e:
    print(f"Kind validation failed: {e}")
```

### Skipping Validation

In some cases, you may want to skip validation:

```python
# Skip validation on creation
structure = StructureData(**structure_dict, validate_kinds=False) # Default behavior
```

:::{warning}
Skipping validation means you take responsibility for ensuring kind consistency. Use this only when you have a specific reason (e.g., asymmetric magnetic structures where you want manual control).
:::

## Working with Kinds

### Accessing Kind Information

```python
# Get kind names for all sites
print(structure.properties.kind_names)  # ['Fe1', 'Fe1', 'O1', 'O1']

# Get the kinds objects
for kind in structure.properties.kinds:
    print(f"Kind: {kind.kind_name}")
    print(f"  Symbol: {kind.symbol}")
    print(f"  Positions: {kind.positions}")
    print(f"  Site indices: {kind.site_indices}")
```

### Kind-Based Representation

Convert to a compressed kind-based format:

```python
# Get structure in kind-based format
kind_based = structure.to_kinds_based(tolerance=1e-3)

# This stores properties per kind instead of per site
# Useful for plugin compatibility and efficient storage
```

## Use Cases

### Case 1: Magnetic Structures

Different spin orientations require different kinds:

```python
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[4.0, 0, 0], [0, 4.0, 0], [0, 0, 4.0]],
    "sites": [
        {"symbol": "Mn", "position": [0, 0, 0], "magmom": [3.0, 0, 0], "kind_name": "Mn_x"},
        {"symbol": "Mn", "position": [2, 0, 0], "magmom": [0, 3.0, 0], "kind_name": "Mn_y"},
        {"symbol": "Mn", "position": [0, 2, 0], "magmom": [0, 0, 3.0], "kind_name": "Mn_z"},
    ],
}

# Three different kinds despite same chemical symbol
structure = StructureData(**structure_dict)
print(len(structure.properties.kinds))  # 3 kinds
```

### Case 2: Charged Systems

Different oxidation states need different kinds:

```python
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]],
    "sites": [
        {"symbol": "Fe", "position": [0, 0, 0], "charge": 2.0, "kind_name": "Fe2+"},
        {"symbol": "Fe", "position": [2.5, 2.5, 2.5], "charge": 3.0, "kind_name": "Fe3+"},
    ],
}

structure = StructureData(**structure_dict)
```

### Case 3: Alloys

Alloy compositions can define different kinds:

```python
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "sites": [
        {
            "symbol": ["Cu", "Zn"],
            "position": [0, 0, 0],
            "weight": (0.7, 0.3),  # 70% Cu, 30% Zn
            "kind_name": "CuZn_70_30",
        },
        {
            "symbol": ["Cu", "Zn"],
            "position": [1.5, 1.5, 1.5],
            "weight": (0.5, 0.5),  # 50% Cu, 50% Zn
            "kind_name": "CuZn_50_50",  # Different composition → different kind
        },
    ],
}
```

## Best Practices

### ✅ DO:

- Use `generate_kinds()` for automatic kind detection
- Use property-specific tolerances
- Validate kinds before storing in database
- Use meaningful kind names for manual assignment

### ❌ DON'T:

- Assign the same kind name to sites with different properties
- Use overly strict tolerances (may create too many kinds)
- Use overly loose tolerances (may incorrectly merge distinct sites)
- Skip validation without good reason
- Modify kind names directly without updating properties

## Performance Considerations

- **Kind-based storage**: More efficient for large structures with many equivalent atoms
- **Database queries**: Kinds enable efficient querying by atomic properties
- **Plugin compatibility**: Some codes expect kind-based input

```python
# For a structure with 1000 Cu atoms with identical properties
# Without kinds: Store 1000 × (all properties)
# With kinds: Store 1 kind + 1000 site indices
# → Significant storage reduction!
```
