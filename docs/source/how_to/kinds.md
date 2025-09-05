## Understanding Kinds

The **kinds system** is a key feature that groups atoms with identical properties:

```python
# Check if structure has kinds
if structure.properties.kinds:
    print(f"Number of kinds: {len(structure.properties.kinds)}")
    for kind in structure.properties.kinds:
        print(f"Kind {kind.kind_name}: {kind.symbol}")
        print(f"  Site indices: {kind.site_indices}")
        print(f"  Number of positions: {len(kind.positions)}")
```

Benefits of kinds:
- **Storage efficiency**: Repeated atoms stored once
- **Performance**: Faster operations on large structures
- **Organization**: Clear grouping of identical atoms
