# How to Migrate Your Plugin to Support aiida-atomistic

This guide explains how to migrate your existing AiiDA plugin to use the new atomistic `StructureData` from the `aiida-atomistic` package.

## Overview

The new `aiida-atomistic` package introduces a modernized `StructureData` class with several key differences from the legacy `orm.StructureData`:

1. **Properties attribute**: All structure information is accessed via a `properties` attribute (a Pydantic `BaseModel`)
2. **Immutability**: `StructureData` is immutable by default (use `StructureBuilder` for modifications)
3. **Site-based approach**: Properties are defined per site, not via a separate `Kind` class
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

For convenience, these properties are also available directly on the structure object:

```python
# Also works (via GetterMixin)
cell = structure.cell
pbc = structure.pbc
sites = structure.sites
```

### Getting Supported Properties

To see all available properties:

```python
from aiida_atomistic import StructureData

# Get all supported properties
all_props = StructureData.get_supported_properties()
print(all_props)
# {'global': {'cell', 'pbc', 'sites', ...}, 'site': {'symbol', 'position', 'mass', ...}}
```

### Immutability

The new `StructureData` is immutable even before storing in the database:

```python
from aiida_atomistic import StructureData, StructureBuilder

# Immutable - cannot modify
structure = StructureData(**structure_dict)
# structure.properties.cell = new_cell  # ❌ Raises error

# Mutable - can modify
mutable = StructureBuilder(**structure_dict)
mutable.set_cell(new_cell)  # ✅ Works

# Convert mutable back to immutable
structure = StructureData.from_builder(mutable)
```

### Site-Based Approach: Kind Class is Dropped

Properties are now defined per site. The `Kind` class is no longer used for input, though kinds can be generated on demand:

```python
structure_dict = {
    'cell': [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    'pbc': [True, True, True],
    'sites': [
        {
            'symbol': 'Fe',
            'position': [0, 0, 0],
            'magmom': [0, 0, 2.2],  # Properties defined per site
            'kind_name': 'Fe1',  # Optional
        },
        {
            'symbol': 'Fe',
            'position': [1.5, 1.5, 1.5],
            'magmom': [0, 0, -2.2],
            'kind_name': 'Fe2',
        },
    ],
}

structure = StructureData(**structure_dict)

# Generate kinds automatically if needed
structure_mutable = structure.to_mutable()
structure_mutable.generate_kinds(tolerance=1e-3)
```

## Validating Structure Properties in Your Plugin

### The Problem

Your plugin likely supports only a subset of all possible structure properties. For example:
- A classical MD code might not support magnetic moments (`magmoms`)
- A DFT code might not support custom properties
- Some codes don't support alloys or vacancies

If a user provides a structure with unsupported properties, your plugin should fail early with a clear error message.

### The Solution: Property Validation in CalcJobs

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

#### Step 2: Add Validation Logic

Implement validation in the `validate_inputs` classmethod:

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

### Real-World Example: aiida-quantumespresso

Here's the actual implementation from `aiida-quantumespresso`'s `BasePwCpInputGenerator`:

```python
class BasePwCpInputGenerator(CalcJob):
    """Base CalcJob for pw.x and cp.x of Quantum ESPRESSO."""

    supported_properties = [
        'cell', 'pbc', 'sites', 'symbols', 'positions',
        'kind_names', 'masses', 'weights', 'hubbard', 'tot_charge'
    ]

    @classmethod
    def validate_inputs(cls, value, port_namespace):
        """Validate the entire inputs namespace."""

        # Skip if ports are excluded (for wrapping processes)
        if any(key not in port_namespace for key in ('pseudos', 'structure')):
            return

        # Check if using atomistic StructureData
        if not isinstance(value['structure'], LegacyStructureData):
            from aiida_atomistic.data.structure.utils import check_plugin_unsupported_props

            plugin_check = check_plugin_unsupported_props(value['structure'], cls.supported_properties)

            if len(plugin_check) > 0:
                raise NotImplementedError(
                    f'The input structure contains one or more unsupported properties '
                    f'for this process: {plugin_check}'
                )

        # QE doesn't support alloys or vacancies
        if value['structure'].is_alloy or value['structure'].has_vacancies:
            raise exceptions.InputValidationError(
                'The structure is an alloy or has vacancies. This is not allowed for '
                'aiida-quantumespresso input structures.'
            )

        # Validate pseudopotentials match structure kinds
        structure_kinds = set(value['structure'].get_kind_names())
        pseudo_kinds = set(value['pseudos'].keys())

        if structure_kinds != pseudo_kinds:
            return f'The `pseudos` and structure kinds do not match: {pseudo_kinds} vs {structure_kinds}'
```

## Supporting Custom Properties

Custom properties are stored in the `custom` dictionary of the structure. If your plugin supports custom properties, add `"custom"` to your `supported_properties` list:

```python
class MyCalculation(CalcJob):

    supported_properties = [
        'cell', 'pbc', 'sites', 'symbols', 'positions',
        'custom',  # ← Allow custom properties
    ]
```

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

### Accessing Custom Properties in Your Plugin

In your `prepare_for_submission` method:

```python
def prepare_for_submission(self, folder):
    structure = self.inputs.structure

    # Access custom properties
    if hasattr(structure.properties, 'custom') and structure.properties.custom:
        custom_data = structure.properties.custom

        # Use in input file generation
        if 'special_setting' in custom_data:
            value = custom_data['special_setting']
            # Write to input file...
```

## Migration Checklist

Use this checklist when migrating your plugin:

### Preparation
- [ ] Review which structure properties your code actually uses
- [ ] Identify which properties your code supports vs. doesn't support
- [ ] Check if your code supports alloys and vacancies
- [ ] Review how you currently access structure data

### Code Changes
- [ ] Add `aiida-atomistic` to your plugin's dependencies
- [ ] Define `supported_properties` class attribute in your CalcJob(s)
- [ ] Import `check_plugin_unsupported_props` from `aiida_atomistic.data.structure.utils`
- [ ] Implement property validation in `validate_inputs` classmethod
- [ ] Update structure property access to use `structure.properties.X` or `structure.X`
- [ ] Handle both legacy and atomistic StructureData during transition
- [ ] If needed, add `"custom"` to supported properties

### Testing
- [ ] Test with structures containing only supported properties (should work)
- [ ] Test with structures containing unsupported properties (should fail with clear error)
- [ ] Test with alloys/vacancies if not supported (should fail with clear error)
- [ ] Test with custom properties if supported
- [ ] Test backward compatibility with legacy `orm.StructureData`

### Documentation
- [ ] Document which structure properties your plugin supports
- [ ] Add examples showing supported property usage
- [ ] Document error messages for unsupported properties
- [ ] Update migration guide for users of your plugin

## Benefits of Property Validation

Implementing proper property validation provides:

1. **Early failure**: Calculations fail at submission, not during execution
2. **Clear errors**: Users immediately know what went wrong
3. **Resource efficiency**: No wasted compute time on incompatible inputs
4. **Better UX**: Users understand limitations upfront
5. **Preserved provenance**: Failed attempts are recorded in the graph

## Common Patterns

### Pattern 1: Subclass with Different Properties

If different calculations in your plugin support different properties:

```python
class BaseMyCalculation(CalcJob):
    """Base class with common properties."""

    supported_properties = [
        'cell', 'pbc', 'sites', 'symbols', 'positions', 'kind_names',
    ]

class MyDFTCalculation(BaseMyCalculation):
    """DFT calculation with magnetic support."""

    supported_properties = BaseMyCalculation.supported_properties + [
        'magmoms', 'charges', 'hubbard',
    ]

class MyMDCalculation(BaseMyCalculation):
    """MD calculation - no magnetic properties."""

    supported_properties = BaseMyCalculation.supported_properties + [
        'masses', 'charges',
    ]
```

### Pattern 2: Conditional Support

Some properties might be conditionally supported based on input parameters:

```python
@classmethod
def validate_inputs(cls, value, port_namespace):
    """Validate inputs."""

    # Base supported properties
    supported = set(cls.supported_properties)

    # Add magnetic support if requested
    parameters = value.get('parameters', {}).get_dict()
    if parameters.get('SYSTEM', {}).get('nspin', 1) == 2:
        supported.add('magmoms')

    # Now validate
    from aiida_atomistic.data.structure.utils import check_plugin_unsupported_props
    unsupported = check_plugin_unsupported_props(value['structure'], supported)

    if unsupported:
        raise NotImplementedError(f'Unsupported properties: {unsupported}')
```

## Backward Compatibility

During the transition period, support both structure types:

```python
from aiida.orm import StructureData as LegacyStructureData
from aiida_atomistic import StructureData

class MyCalculation(CalcJob):

    @classmethod
    def define(cls, spec):
        super().define(spec)
        # Accept both types
        spec.input('structure',
                  valid_type=(LegacyStructureData, StructureData),
                  help='Input structure (legacy or atomistic)')

    @classmethod
    def validate_inputs(cls, value, port_namespace):
        """Validate inputs."""

        structure = value.get('structure')

        # Only validate atomistic structures
        if isinstance(structure, StructureData):
            from aiida_atomistic.data.structure.utils import check_plugin_unsupported_props
            unsupported = check_plugin_unsupported_props(structure, cls.supported_properties)
            if unsupported:
                raise NotImplementedError(f'Unsupported properties: {unsupported}')

        # Legacy structures pass through
        # (or convert them: structure = structure.to_atomistic())
```

## Further Reading

- [How to Add Properties](dev_adding_properties.md) - Adding new properties to aiida-atomistic
- [Kinds Documentation](kinds.md) - Understanding kinds and tolerances
- [Immutability Guide](../in_depth/immutability.md) - Working with immutable structures
- [Pydantic Documentation](https://docs.pydantic.dev/) - Understanding the underlying validation framework
