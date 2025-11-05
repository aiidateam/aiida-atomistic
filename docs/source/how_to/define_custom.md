# Adding Custom Properties

This guide explains how to define custom properties in a `StructureData` or `StructureBuilder` instance.

:::{note}
Custom properties in the `custom` dict won't have:
- Automatic validation
- Dedicated getter/setter methods
- Integration with kinds or compression

Use them for plugin-specific experimental properties that doesn't need full integration.
:::

For properties that don't fit the standard patterns, use the `custom` dictionary:

```python
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "sites": [...],
    "custom": {
        "my_special_property": "some_value",
        "another_custom_field": [1, 2, 3],
    }
}

structure = StructureData(**structure_dict)
print(structure.properties.custom["my_special_property"])
```
