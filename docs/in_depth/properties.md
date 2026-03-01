# Structure Properties

This guide explains the property system in aiida-atomistic, including property types, formats, and how to access them.

## Overview

The structure in aiida-atomistic is **site-based**, meaning the fundamental unit of information is the `Site` object. Properties fall into three categories:

1. **Site Properties**: Properties stored per atomic site (e.g., `symbol`, `position`, `charge`)
2. **Global Properties**: Properties that apply to the entire structure (e.g., `pbc`, `cell`)
3. **Computed Properties**: Properties calculated from other properties (e.g., `formula`, `cell_volume`)

## Quick Reference: Discovering Properties at Runtime

Four methods let you inspect the full property system programmatically at any time:

| Method | Called on | Returns | Use when you want to know… |
|---|---|---|---|
| `get_supported_properties()` | class | `dict` with keys `'global'` and `'site'` | What properties *can* be set at all |
| `get_computed_properties()` | class | `set` of names | Which properties are *derived* (never set by the user) |
| `get_defined_properties()` | instance | `set` of names | Which properties are *actually set* on this structure |
| `get_queryable_properties()` | class | `dict` with keys `'queryable'` / `'not_queryable'` | Which properties can be filtered with `QueryBuilder` |

```python
from aiida_atomistic.data import StructureData

# 1. What properties can be set?
supported = StructureData.get_supported_properties()
# supported['global'] → {'pbc', 'cell', 'sites', 'tot_charge', 'tot_magnetization', 'hubbard', 'custom'}
# supported['site']   → {'symbol', 'position', 'mass', 'charge', 'magmom', 'magnetization', 'weight', 'kind_name', ...}

# 2. Which properties are computed (i.e. derived, never user-set)?
computed = StructureData.get_computed_properties()
# → {'formula', 'cell_volume', 'dimensionality', 'is_alloy', 'has_vacancies',
#    'composition', 'n_sites', 'n_kinds', 'positions', 'symbols', 'masses',
#    'charges', 'magmoms', 'magnetizations', 'weights', 'kind_names', 'kinds',
#    'max_charge', 'min_charge', 'max_magmom', 'min_magmom',
#    'max_magnetization', 'min_magnetization'}

# 3. What is actually set on a specific structure instance?
defined = structure.get_defined_properties()
# → {'cell', 'pbc', 'sites', 'positions', 'symbols', 'masses', ...}
#   Pure computed fields without a singular_form (formula, cell_volume, …) are excluded by default.
#   Pass exclude_computed_without_singular=False to include them all.

# 4. What can be queried in the AiiDA database?
queryable = StructureData.get_queryable_properties()
# queryable['queryable']     → properties stored as DB attributes  → can filter with QueryBuilder
# queryable['not_queryable'] → properties stored in .npz files     → cannot be queried directly
```

!!! note
    `get_defined_properties()` accepts two keyword arguments for finer control:

    - `exclude_computed_without_singular=False` — also returns pure computed fields such as `formula`, `cell_volume`, `is_alloy`
    - `exclude_computed=True` — returns only the raw user-set base fields (`cell`, `pbc`, `sites`)



### 1. Site Properties

Each `Site` object can have the following properties:

#### Basic Site Properties

- **`symbol`**: Chemical element symbol

    - Type: `str` for pure elements, `list[str]` for alloys
    - Example: `'Cu'` or `['Cu', 'Zn']`
  
- **`position`**: Atomic coordinates in Cartesian space

    - Type: `np.ndarray` (shape: `(3,)`)
    - Example: `[0.0, 0.0, 0.0]`

- **`mass`**: Atomic mass

    - Type: `float` or `None` (defaults to standard atomic mass)
    - Example: `63.546` for Cu

#### Advanced Site Properties

- **`charge`**: Atomic charge
    - Type: `float` or `None`
    - Example: `1.0` for Cu⁺

- **`magmom`**: Magnetic moment vector (non-collinear magnetism)

    - Type: `np.ndarray` (shape: `(3,)`) or `None`
    - Example: `[0.0, 0.0, 2.2]`
    - ⚠️ **Mutually exclusive with `magnetization`**

- **`magnetization`**: Scalar magnetization (collinear magnetism)

    - Type: `float` or `None`
    - Example: `2.2`
    - ⚠️ **Mutually exclusive with `magmom`**

- **`weight`**: Occupancy weights for alloys/vacancies

    - Type: `list[float]` or `None`
    - Example: `[0.7, 0.3]` for 70% Cu, 30% Zn
    - Must sum to ≤ 1.0 (sum < 1.0 indicates vacancy)

- **`kind_name`**: Kind identifier for grouping similar sites

    - Type: `str` or `None`
    - Example: `'Cu1'`
    - See [Kinds Documentation](kinds.md) for details

??? warning "Mutual exclusivity of magnetic properties"

    For each site, you can set **either** `magmom` (vector) **or** `magnetization` (scalar), but not both:

    - **`magmom`**: For non-collinear magnetic structures (spin-orbit coupling, complex spin textures)
    - **`magnetization`**: For collinear magnetic structures (simple up/down spins along one axis)

    Setting both will raise a validation error.


### 2. Global Properties

Properties that apply to the entire structure:

#### Structural Properties

- **`pbc`**: Periodic boundary conditions
    - Type: `list[bool]` (length 3)
    - Example: `[True, True, False]` for 2D slab

- **`cell`**: Lattice vectors defining the unit cell
    - Type: `np.ndarray` (shape: `(3, 3)`)
    - Example: `[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 5.0]]`

#### Global Physical Properties

- **`tot_charge`**: Total charge of the structure
    - Type: `float` or `None`
    - Example: `2.0`

- **`tot_magnetization`**: Total magnetization of the structure
    - Type: `float` or `None`
    - Example: `4.4`

#### Hubbard Parameters

- **`hubbard`**: Hubbard model parameters (DFT+U, DFT+U+V)
    - Type: `HubbardStructureData` object or `None`
    - Contains site-indexed U and V parameters
    - See [Hubbard Documentation](hubbard.md) for details

!!! note
    `hubbard` is a global property because Hubbard parameters reference specific site indices:

    - **On-site U**: Applied to a specific site (e.g., site 0)
    - **Inter-site V**: Couples two specific sites (e.g., sites 0 and 1)

    This makes it inherently a structure-level property rather than a per-site property.


### 3. Computed Properties

Properties automatically calculated from other properties. These fall into two subcategories:

#### Stored Computed Properties (for querying)

These are computed but stored in the database for efficient querying:

**Structural Computed Properties:**

- **`cell_volume`**: Volume of the unit cell
    - Type: `float`
    - Calculated from: `cell`
    - Example: `27.0` (for 3×3×3 cubic cell)

- **`dimensionality`**: Structure dimensionality
    - Type: `int` (0, 1, 2, or 3)
    - Calculated from: `pbc` and `cell`
    - Example: `3` for 3D bulk, `2` for 2D slab

- **`formula`**: Chemical formula (Hill notation by default)
    - Type: `str`
    - Calculated from: `symbols`
    - Example: `'H2O'`, `'BaTiO3'`

**Composition Indicators:**

- **`is_alloy`**: Whether any site contains multiple elements
    - Type: `bool`
    - Example: `True` if any site has `symbol=['Cu', 'Zn']`

- **`has_vacancies`**: Whether any site has occupancy < 1
    - Type: `bool`
    - Example: `True` if any site has `weight=[0.9]`

- **`n_sites`**: Total number of sites
    - Type: `int`
    - Example: `8`

**Statistical Properties (for range queries):**

- **`max_charge`**, **`min_charge`**: Charge extrema
- **`max_magmom`**, **`min_magmom`**: Magnetic moment magnitude extrema
- **`max_magnetization`**, **`min_magnetization`**: Magnetization extrema

???+ tip
    Statistical properties enable efficient database queries like "find all structures with charge between 0 and 2". See [Querying Guide](../how_to/query.md).


#### Computed Array Properties (aggregated from sites)

These properties aggregate site-level data into arrays. They use **plural names** to distinguish them from singular site properties:

| Plural Property | Singular Source | Type | Shape |
|----------------|----------------|------|-------|
| `positions` | `site.position` | `np.ndarray` | `(N, 3)` |
| `symbols` | `site.symbol` | `list[str]` | `(N,)` |
| `masses` | `site.mass` | `np.ndarray` | `(N,)` |
| `charges` | `site.charge` | `np.ndarray` or `None` | `(N,)` |
| `magmoms` | `site.magmom` | `np.ndarray` or `None` | `(N, 3)` |
| `magnetizations` | `site.magnetization` | `np.ndarray` or `None` | `(N,)` |
| `kind_names` | `site.kind_name` | `list[str]` or `None` | `(N,)` |
| `weights` | `site.weight` | `list[list]` or `None` | `(N, ?)` |

??? note "Naming Convention"
    - **Singular** (`charge`, `position`): Access individual site property
    - **Plural** (`charges`, `positions`): Access all sites' properties as array

Example:
```python
structure.properties.sites[0].charge  # Single value for site 0
structure.properties.charges[0]       # Same value from aggregated array
structure.properties.charges          # All charges as numpy array
```
:::

#### Reconstructed Properties (on-the-fly)

These are computed dynamically when accessed:

- **`kinds`**: Grouped site information based on `kind_names`
  - Type: `list[Kind]` or `None`
  - Groups sites with the same `kind_name`
  - Each `Kind` contains: positions, site indices, and shared properties
  - See [Kinds Documentation](kinds.md)

## Accessing Properties

### Via Structure Object

```python
from aiida_atomistic.data.structure import StructureData

# Create structure
structure = StructureData(
    cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    pbc=[True, True, True],
    sites=[
        {'symbol': 'Cu', 'position': [0, 0, 0], 'charge': 1.0},
        {'symbol': 'O', 'position': [1.5, 1.5, 1.5], 'charge': -2.0},
    ]
)

# Access global properties
structure.properties.cell        # 3×3 array
structure.properties.pbc         # [True, True, True]

# Access computed properties
structure.properties.formula     # 'CuO'
structure.properties.cell_volume # 27.0
structure.properties.n_sites     # 2

# Access individual site
site = structure.properties.sites[0]
site.symbol                      # 'Cu'
site.position                    # [0, 0, 0]
site.charge                      # 1.0

# Access aggregated arrays (plural)
structure.properties.symbols     # ['Cu', 'O']
structure.properties.positions   # [[0, 0, 0], [1.5, 1.5, 1.5]]
structure.properties.charges     # [1.0, -2.0]
```

### Via Legacy Accessors (Backward Compatibility)

For compatibility with aiida-core's `StructureData`, shorthand accessors are available:

```python
# These are equivalent:
structure.properties.cell   == structure.cell     # True
structure.properties.pbc    == structure.pbc      # True
structure.properties.sites  == structure.sites    # True
structure.properties.kinds  == structure.kinds    # True
structure.properties.formula == structure.formula # True
```

## Property Validation

### Automatic Validation

All properties are validated when set:

```python
# ✅ Valid: proper element symbol
site = {'symbol': 'Cu', 'position': [0, 0, 0]}

# ❌ Invalid: unknown element
site = {'symbol': 'Xx', 'position': [0, 0, 0]}  # Raises ValueError

# ❌ Invalid: both magmom and magnetization
site = {
    'symbol': 'Fe',
    'position': [0, 0, 0],
    'magmom': [0, 0, 2.2],
    'magnetization': 2.2  # Error: mutually exclusive
}

# ❌ Invalid: weights sum > 1
site = {
    'symbol': ['Cu', 'Zn'],
    'weight': [0.7, 0.5],  # Sum = 1.2 > 1.0, raises ValueError
    'position': [0, 0, 0]
}
```

### Manual Validation

```python
# Check if sites are too close (< 0.001 Å)
from aiida_atomistic.data.structure.utils import _check_valid_sites

sites = [
    {'symbol': 'H', 'position': [0, 0, 0]},
    {'symbol': 'H', 'position': [0.0001, 0, 0]},
]
_check_valid_sites(sites)  # Raises ValueError if too close
```

## Property Querying

Stored computed properties and statistical properties enable efficient database queries:

```python
from aiida import orm
from aiida_atomistic.data.structure import StructureData

# Query by formula
structures = orm.QueryBuilder().append(
    StructureData,
    filters={'attributes.formula': 'H2O'}
).all()

# Query by charge range (using statistical properties)
structures = orm.QueryBuilder().append(
    StructureData,
    filters={
        'attributes.max_charge': {'>=': 0, '<=': 2}
    }
).all()

# Query by dimensionality
slabs = orm.QueryBuilder().append(
    StructureData,
    filters={'attributes.dimensionality': 2}
).all()
```

See the [Querying Guide](../how_to/query.md) for more examples.

## Property Metadata

Each property has metadata that controls its behavior:

```python
from aiida_atomistic.data.structure.models import StructureBaseModel

# Get property metadata
field_info = StructureBaseModel.model_fields['cell']
print(field_info.json_schema_extra)  # {'store_in': 'db'}

# Properties with 'singular_form' are site properties
field_info = StructureBaseModel.model_computed_fields['charges']
print(field_info.json_schema_extra)  
# {'store_in': 'repository', 'singular_form': 'charge'}
```

### Metadata Fields

- **`store_in`**: Where to store the property
  - `'db'`: Database attributes (fast queries, size-limited)
  - `'repository'`: File repository (large arrays, slower queries)
  
- **`singular_form`**: Links plural computed property to singular site property
  - Example: `charges` (plural) ↔ `charge` (singular)
  
- **`statistic`**: Statistical aggregation for querying
  - `'max'`: Maximum value across all sites
  - `'min'`: Minimum value across all sites

## Best Practices

### 1. Choose the Right Property Type

```python
# ✅ Use magnetization for collinear systems
site = {'symbol': 'Fe', 'position': [0, 0, 0], 'magnetization': 2.2}

# ✅ Use magmom for non-collinear systems
site = {'symbol': 'Fe', 'position': [0, 0, 0], 'magmom': [1.5, 1.5, 1.0]}

# ❌ Don't use both
site = {
    'symbol': 'Fe',
    'position': [0, 0, 0],
    'magnetization': 2.2,
    'magmom': [0, 0, 2.2]  # Error!
}
```

### 2. Use Kinds for Repeated Sites

If many sites share the same properties, use kinds to reduce duplication:

```python
# Without kinds: repetitive
sites = [
    {'symbol': 'Cu', 'position': [0, 0, 0], 'charge': 1.0, 'mass': 63.546},
    {'symbol': 'Cu', 'position': [2, 0, 0], 'charge': 1.0, 'mass': 63.546},
    {'symbol': 'Cu', 'position': [4, 0, 0], 'charge': 1.0, 'mass': 63.546},
]

# With kinds: efficient
sites = [
    {'symbol': 'Cu', 'position': [0, 0, 0], 'kind_name': 'Cu1'},
    {'symbol': 'Cu', 'position': [2, 0, 0], 'kind_name': 'Cu1'},
    {'symbol': 'Cu', 'position': [4, 0, 0], 'kind_name': 'Cu1'},
]
# Properties like charge, mass stored once per kind
```

See [Kinds Guide](kinds.md) for details.

### 3. Leverage Computed Properties for Queries

```python
# ✅ Query using stored computed properties
structures = orm.QueryBuilder().append(
    StructureData,
    filters={'attributes.formula': 'CuO'}
).all()

# ❌ Don't manually compute formula for each structure (slow)
all_structures = orm.QueryBuilder().append(StructureData).all()
cuo_structures = [s for s in all_structures if s.properties.formula == 'CuO']
```

### 4. Understand Mutable vs Immutable

```python
from aiida_atomistic.data.structure import StructureBuilder, StructureData

# StructureBuilder: mutable (use during construction)
builder = StructureBuilder(cell=[[3, 0, 0], [0, 3, 0], [0, 0, 3]], pbc=[True]*3)
builder.properties.sites.append({'symbol': 'Cu', 'position': [0, 0, 0]})  # OK

# StructureData: immutable (use for storing in database)
structure = StructureData(cell=[[3, 0, 0], [0, 3, 0], [0, 0, 3]], pbc=[True]*3, sites=[...])
structure.properties.sites.append(...)  # Error: immutable
```