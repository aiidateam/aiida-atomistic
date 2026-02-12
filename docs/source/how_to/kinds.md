# Kinds and Automatic Kind Generation

In crystallography and materials science, **kinds** represent groups of atoms that share the same chemical and physical properties. Atoms of the same kind have:

- Same chemical symbol
- Same mass
- Same charge
- Same magnetic moment (magnitude and direction)
- Same additional properties

Often, simulation codes use kind-based representations in their input files.

## Basics

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
            "kind_name": "Fe2",  # Different kind due to different magmom
        },
    ],
}

structure = StructureData(**structure_dict)
print(structure.properties.kind_names)  # ['Fe1', 'Fe2']
```

## Generating a structure with automatically generated kinds

It is possible to automatically generate the kinds, starting from an initialised structure.
For both `StructureData` and `StructureBuilder`, we provide a `to_kinds` method, which will
return as output a new instance of the same object, but this time with the kinds defined as detected
by the implemented algorithm.

```python
# Generate kinds automatically
new_structure = structure.to_kinds()
```

the `new_structure` object will be an instance of the same class as the starting object.
In the case of the AiiDA `StructureData`, the new structure will be stored in the database (and created by means of a `calcfunction`) to preserve provenance. It is possible to skip the provenance by providing the `store_provenance=False` input parameter (e.g.: `new_structure = structure.to_kinds(store_provenance=False)`).

### Thresolds for kinds detection

Thresholds control how strictly properties must match for sites to be considered the same kind.
Each property in the `Site` model has a default threshold value stored in its field metadata.
You can access these default thresholds programmatically:

```python
from aiida_atomistic.data.structure.site import Site

# Get all default thresholds
default_thresholds = Site.get_default_thresholds()
print(default_thresholds)
# {'mass': 0.001, 'charge': 0.01, 'magmom': 0.01, 'magnetization': 0.01, 'weight': 0.01}
```

When you call `to_kinds()` without specifying the `threshold` input parameter, these property-specific defaults are used automatically.

#### Custom thresolds

You can override the defaults by specifying a dictionary with specific thresholds for the properties of interest:

```python
structure.to_kinds(threshold={'charge':0.005})
```

This approach gives you fine-grained control while maintaining sensible defaults for properties you don't specify.

:::{note}
Available threshold keys can be inspected using the `Site.get_default_thresholds()` method.
:::

## Validation of the defined kinds

If kinds are defined in your structure, it is always possible to validate them, to ensure they will work as expected.
This can be done through the `validate_kinds` method:

```python
structure = StructureBuilder(**structure_dict)

# Validate the current kind assignments
try:
    structure.validate_kinds()
    print("Kinds are valid!")
except ValueError as e:
    print(f"Kind validation failed: {e}")
```

you can pass, as argument, a threshold `dict` as for the `to_kinds` method.

### Accessing Kind Information

```python
# Get kind names for all sites
print(structure.properties.kind_names)  # ['Fe1', 'Fe2',]

# Get the kinds objects
for kind in structure.properties.kinds:
    print(f"Kind: {kind.kind_name}")
    print(f"  Symbol: {kind.symbol}")
    print(f"  Positions: {kind.positions}")
    print(f"  Site indices: {kind.site_indices}")
```

**Output**
```
['Fe1', 'Fe2']
Kind: Fe1
  Symbol: Fe
  Positions: [[0. 0. 0.]]
  Site indices: [0]
Kind: Fe2
  Symbol: Fe
  Positions: [[2.5 2.5 2.5]]
  Site indices: [1]
```

Note the kinds can be also accessed directly via `structure.kinds`.
