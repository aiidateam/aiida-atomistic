# How to Migrate Your Plugin to Support aiida-atomistic

This guide explains how to migrate your existing AiiDA plugin to use the new atomistic `StructureData` from the `aiida-atomistic` package.

## Overview

The new `aiida-atomistic` package introduces a modernized `StructureData` class with several key differences from the legacy `orm.StructureData`:

1. **Properties attribute**: All structure information is accessed via a `properties` attribute (a [Pydantic](https://docs.pydantic.dev/latest/) `BaseModel` subclass)
2. **Immutability**: `StructureData` is immutable by default (use `StructureBuilder` for modifications)
3. **Site-based approach**: Properties are defined per site, not via a separate `Kind` class (which is optional)
4. **Validation**: Built-in Pydantic validation for all properties

## Main Changes from orm.StructureData

### Accessing Structure Properties

All properties are now accessed through the `properties` attribute:

```python
# Old way (orm.StructureData)
cell = structure.cell
pbc = structure.pbc
sites = structure.sites

# New way (atomistic StructureData)
cell = structure.properties.cell
pbc = structure.properties.pbc
sites = structure.properties.sites
```

For convenience (and simpler plugin migration), these properties are also available directly on the structure object:

```python
# This als works
cell = structure.cell
pbc = structure.pbc
sites = structure.sites
```

### Immutability

The new `StructureData` is immutable even before storing in the database.
The following will raise error:

```python
from aiida_atomistic import StructureData, StructureBuilder

# Immutable - cannot modify
structure = StructureData(**structure_dict)
structure.properties.cell = new_cell  # Raises error
```

To modify a property, you need to pass through the `StructureBuilder`, as explaned in the [dedicated section](../how_to/creation_mutation.md).

### Site-Based Approach: kinds are and optional property

Properties are now defined per site, and the `Kind` class is no longer defined by default.
If required, kinds can be defined or generated automatically. For more details please see the [dedicated section](../how_to/kinds.md).

## Validating Structure Properties in Your Plugin

Your plugin likely supports only a subset of all possible structure properties. A DFT code might not support custom properties, some codes don't support alloys or vacancies, and so on.

If a user provides a structure with unsupported properties, your plugin should fail early with a clear error message. The idea is that in principle, all the defined properties should be used in the calculation.

### Property Validation in CalcJobs

The recommended approach is to validate properties in your `CalcJob`'s `validate_inputs` classmethod. This is the pattern used in `aiida-quantumespresso`.

#### Step 1: Define Supported Properties

Add a class attribute listing all properties your code supports:

```python
from aiida.engine import CalcJob

class MyCalculation(CalcJob):
    """CalcJob for my simulation code."""

    # Define which properties this calculation supports
    supported_properties = [
        'cell',        # Required: crystal structure
        'pbc',         # Required: periodic boundary conditions
        'sites',       # Required: atomic sites
        'symbols',     # Required: chemical symbols
        'positions',   # Required: atomic positions
        'kind_names',  # Required: kind identifiers
        'masses',      # Optional: custom atomic masses
        'charges',     # Optional: atomic charges
        # 'magmoms',   # NOT supported - no magnetic calculations
        # 'hubbard',   # NOT supported - no DFT+U
    ]
```

!!! note "**Use Plural Forms for Site Properties**"

    When defining `supported_properties`, you must use the **plural form** for site-based properties (properties that vary per atom).
    For example:

    - `'charges'` (not `'charge'`)
    - `'masses'` (not `'mass'`)
    - `'magmoms'` (not `'magmom'`)
    - `'positions'` (not `'position'`)

    Global properties (that apply to the entire structure) use their standard name:

    - `'cell'`
    - `'pbc'`
    - `'temperature'`

    **How to Find Property Names:**

    To see all available properties and their correct names:

    ```python
    from aiida_atomistic import StructureData

    # Get all supported properties
    props = StructureData.get_supported_properties()

    # Site properties (use plural forms in supported_properties)
    print(props['site'])
    # {'charge', 'mass', 'magmom', 'magnetization', 'weight', ...}

    # Global properties (use as-is in supported_properties)
    print(props['global'])
    # {'cell', 'pbc', 'tot_charge', 'temperature', ...}

    # Computed properties (arrays from site properties - use plural)
    print(props['computed'])
    # {'charges', 'masses', 'magmoms', 'positions', 'symbols', ...}
    ```

    **Why Plural?**

    Site properties in the `Site` model are singular (`charge`, `mass`), but they're accessed as arrays through computed fields with plural names (`charges`, `masses`). The validation checks for the array forms since that's what your plugin actually uses:

    ```python
    # In your plugin, you access:
    structure.properties.charges  # Array of all charges, what you will use
    # Not:
    structure.properties.sites[0].charge  # Individual site charge (you don't validate this)
    ```


#### Step 2: Add Validation Logic

Implement validation in the `validate_inputs` classmethod, using the `check_plugin_unsupported_props` function:

```python
from aiida.common import exceptions

class MyCalculation(CalcJob):

    supported_properties = [
        'cell', 'pbc', 'sites', 'symbols', 'positions',
        'kind_names', 'masses', 'charges',
    ]

    @classmethod
    def validate_inputs(cls, value, port_namespace):
        """Validate the entire inputs namespace."""

        # Skip validation if structure port is excluded
        if 'structure' not in port_namespace:
            return

        # Check if structure input is provided
        if 'structure' not in value:
            return 'required value was not provided for the `structure` namespace.'

        structure = value['structure']

        # Check if using atomistic StructureData (not legacy)
        from aiida.orm import StructureData as LegacyStructureData

        if not isinstance(structure, LegacyStructureData):
            # Import the validation utility
            from aiida_atomistic.data.structure.utils import check_plugin_unsupported_props

            # Get the set of unsupported properties
            unsupported = check_plugin_unsupported_props(structure, cls.supported_properties)

            if len(unsupported) > 0:
                raise NotImplementedError(
                    f'The input structure contains unsupported properties '
                    f'for this calculation: {unsupported}'
                )

        # Additional validations (optional)
        if structure.is_alloy:
            raise exceptions.InputValidationError(
                'This code does not support alloy structures.'
            )

        if structure.has_vacancies:
            raise exceptions.InputValidationError(
                'This code does not support structures with vacancies.'
            )
```

!!! tip
    You can also put the validation in the WorkChains using the given CalcJob, to stop prematurely instead of performing some steps and then exit only when trying to submit with the wrong structure.


!!! tip
    Of course, you will also need to add the logic to write your input file starting from the structure properties, which before were defined in the `parameters` input `orm.Dict` (at least in the aiida-quantumespresso plugin).


### Real-World Example: aiida-quantumespresso

Here's the current (temporary) implementation from `aiida-quantumespresso`'s `BasePwCpInputGenerator`:

```python
class BasePwCpInputGenerator(CalcJob):
    """Base CalcJob for pw.x and cp.x of Quantum ESPRESSO."""

    ...

    supported_properties = [
        'cell', 'pbc', 'sites', 'symbols', 'positions',
        'kind_names', 'masses', 'weights', 'hubbard', 'tot_charge'
    ]

    ...

    @classmethod
    def validate_inputs(cls, value, port_namespace):
        """Validate the entire inputs namespace."""

        # Wrapping processes may choose to exclude certain input ports in which case we can't validate. If the ports
        # have been excluded, and so are no longer part of the ``port_namespace``, skip the validation.
        if any(key not in port_namespace for key in ('pseudos', 'structure')):
            return

        if not isinstance(value['structure'], LegacyStructureData):
            # we have the atomistic StructureData, so we need to check if all the defined properties are supported
            from aiida_atomistic.data.structure.utils import check_plugin_unsupported_props
            plugin_check = check_plugin_unsupported_props(value['structure'], cls.supported_properties)
            if len(plugin_check) > 0:
                raise NotImplementedError(
                    f'The input structure contains one or more unsupported properties \
                    for this process: {plugin_check}'
                )

        if value['structure'].is_alloy or value['structure'].has_vacancies:
            raise exceptions.InputValidationError(
                'The structure is an alloy or has vacancies. This is not allowed for \
                aiida-quantumespresso input structures.'
            )
```

### Supporting Custom Properties

Custom properties are stored in the `custom` dictionary of the structure. If your plugin supports custom properties, add `"custom"` to your `supported_properties` list:

```python
class MyCalculation(CalcJob):

    supported_properties = [
        'cell', 'pbc', 'sites', 'symbols', 'positions',
        'custom',  # ← Allow custom properties
    ]
```

## Benefits of Property Validation

Implementing proper property validation provides:

1. **Early failure**: Calculations fail at submission, not during execution
2. **Better UX**:: Users immediately know what went wrong and understand limitations upfront
