# Adding Custom Properties

This guide explains how to define custom properties in a `StructureData` or `StructureBuilder` instance.

!!! note

    Custom properties in the `custom` dict won't have:

    - Automatic validation
    - Dedicated getter/setter methods
    - Integration with kinds or compression

    Use them for plugin-specific experimental properties that don't need full integration.

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

To add a custom properties on an already initialised `StructureBuilder`, you can directly define `structure.properties.custom` or use the `set_custom` method.
In the latter case, if `structure.properties.custom` is already defined, it will be updated with the new values provided in the `set_custom` method, but other keys will not be removed.

To delete a set of defined custom properties, use the `remove_custom` method, passing as input a list of keys (strings). To remove the entire custom dictionary, you
can call the same method without specifying any input parameter.

### When to Use Custom Properties

Use custom properties when:

- Your code has special parameters that are structure-related but not standard
- You need to pass code-specific data that affects the calculation
- The property will be used in the simulation

### When NOT to Use Custom Properties

Don't use custom properties for:

- Metadata or annotations
- Information not used in the calculation
- Experimental context or provenance

For these cases, use AiiDA extras instead:

```python
structure.base.extras.set("experimental_source", "XRD measurement")
structure.base.extras.set("measurement_date", "2025-11-03")
structure.base.extras.set("notes", "Sample prepared at 500K")
```
