# Structure of the Code

This document explains the architecture of `aiida-atomistic` and how different components work together.

## Overview

`aiida-atomistic` uses a site-based architecture with immutable Data nodes. The key concepts are:

1. **Sites** - Individual atomic/molecular positions with properties
2. **Kinds** - Metadata grouping sites with similar properties
3. **StructureData** - Immutable stored structure
4. **StructureBuilder** - Mutable tool for constructing structures

```
        Sites (with properties)
               ↓
        Pydantic Model
               ↓
     ┌──────────────────┐
     │  StructureData   │  ← Immutable, stored in DB
     └──────────────────┘
               ↑
        StructureBuilder  ← Mutable, for construction
```

## Core Components

### 1. Site Model (`site.py`)

Represents a single atomic/molecular site with properties:

```python
class Site(BaseModel):
    position: tuple[float, float, float]
    kind_name: str
    mass: Optional[float] = None
    charge: Optional[float] = None
    magmom: Optional[float] = None
    # ... other properties
```

**Key Features:**

- Pydantic validation of all properties
- Default values for optional properties
- Threshold-based comparison (e.g., positions within 1e-8)

**Property Behavior:**

```python
site = Site(position=(0, 0, 0), kind_name='Fe', charge=2.5)
# Properties stored directly on site
# Defaults applied automatically: mass, magmom, etc.
```

### 2. Pydantic Models (`models.py`)

Core data structure for structures before storage:

```python
class StructureBaseModel(BaseModel):
    cell: ArrayLike3x3
    pbc: tuple[bool, bool, bool]
    sites: list[Site]
    
    # Computed properties
    @computed_field
    @property
    def positions(self) -> np.ndarray:
        return np.array([site.position for site in self.sites])
```

**Responsibilities:**

- Validate input data (cell, pbc, sites)
- Compute derived properties (formulas, statistics)
- Define storage locations via metadata
- Provide array views of site properties

### 3. StructureData (`structure.py`)

Immutable AiiDA Data node for stored structures:

```python
class StructureData(Data):
    """Stored structure - cannot be modified."""
    
    @property
    def properties(self) -> PropertyGetterMixin:
        """Access all structure properties."""
        return PropertyGetterMixin(self.attributes, self.repository)
```

**Key Points:**

- Inherits from `aiida.orm.Data` - stored in AiiDA database
- Once stored, completely immutable
- Properties accessed via `PropertyGetterMixin`
- Uses `StructureBaseModel` for validation before storage

### 4. StructureBuilder (`builder.py`)

Mutable tool for constructing structures:

```python
builder = StructureBuilder()
builder.add_site(position=(0, 0, 0), kind_name='Fe')
builder.cell = [[3, 0, 0], [0, 3, 0], [0, 0, 3]]
structure = builder.get_structuredata()  # Returns immutable StructureData
```

**Features:**

- Add/remove sites interactively
- Modify cell and pbc
- Convert to `StructureData` when ready
- Useful for scripts and workflows

### 5. PropertyGetterMixin (`getter_mixin.py`)

Provides uniform property access for stored structures:

```python
structure.properties.positions      # From repository
structure.properties.formula        # From database
structure.properties.cell_volume    # Computed
structure.properties.kinds          # Reconstructed
```

**Responsibilities:**

- Load arrays from repository (`.npz` files)
- Retrieve attributes from database
- Cache loaded data
- Reconstruct kinds from stored properties

## Property Flow

### Creating a Structure

```python
# 1. Create sites
sites = [
    Site(position=(0, 0, 0), kind_name='Fe', charge=2.0),
    Site(position=(1, 1, 1), kind_name='O', charge=-1.0)
]

# 2. Create Pydantic model (validation happens here)
model = StructureBaseModel(
    cell=[[3, 0, 0], [0, 3, 0], [0, 0, 3]],
    pbc=(True, True, True),
    sites=sites
)

# 3. Create StructureData (storage happens here)
structure = StructureData(model=model)
structure.store()  # → Database + Repository
```

### Accessing Properties

```python
# After loading from database
structure = orm.load_node(pk)

# Properties route through PropertyGetterMixin
structure.properties.positions   # Loads from repository
structure.properties.formula     # Reads from database
structure.properties.kinds       # Reconstructs from stored data
```

## Storage Architecture

### Database Storage

Small properties stored as AiiDA attributes:

```python
structure.base.attributes.get('cell')       # [[3,0,0], [0,3,0], [0,0,3]]
structure.base.attributes.get('formula')    # 'FeO'
structure.base.attributes.get('n_sites')    # 2
```

### Repository Storage

Large arrays stored in `.npz` files:

```python
# In ~/.aiida/repository/<profile>/node/<uuid>/properties.npz
{
    'positions': [[0,0,0], [1,1,1]],
    'charges': [2.0, -1.0],
    'masses': [55.845, 15.999]
}
```

### Storage Metadata

Each property has metadata in `models.py`:

```python
@computed_field(
    json_schema_extra={
        "store_in": "repository",      # Where to store
        "singular_form": "charge"      # How to reconstruct sites
    }
)
@property
def charges(self) -> np.ndarray:
    return np.array([site.charge for site in self.sites])
```

## Kinds System

Kinds are **metadata**, not stored entities. They group sites with similar properties.

### Automatic Kind Generation

```python
sites = [
    Site(position=(0,0,0), kind_name='Fe', charge=2.0),
    Site(position=(1,1,1), kind_name='Fe', charge=2.0),  # Same kind
    Site(position=(2,2,2), kind_name='O', charge=-1.0)   # Different kind
]
# → Generates 2 kinds: Fe (2 sites), O (1 site)
```

### Kind Reconstruction

When loading from database:

```python
# 1. Load arrays from repository
positions = load_from_npz('positions')
charges = load_from_npz('charges')
kind_names = load_from_attributes('kind_names')

# 2. Reconstruct sites
sites = [
    Site(position=pos, kind_name=name, charge=charge)
    for pos, name, charge in zip(positions, kind_names, charges)
]

# 3. Generate kinds from sites
kinds = generate_kinds_from_sites(sites)
```

## Validation Flow

### Input Validation (Pydantic)

```python
# Invalid cell → ValidationError
StructureBaseModel(
    cell=[[1, 0], [0, 1]],  # Wrong shape
    sites=sites
)
# ❌ Raises: Cell must be 3x3

# Invalid site → ValidationError  
Site(position=(0, 0))  # Wrong shape
# ❌ Raises: Position must be 3D
```

### Storage Validation

```python
# Before storing, checks:
# - All sites have kind_name
# - Required properties present
# - Arrays have consistent lengths

structure.store()  # Validates everything
```

## Key Design Patterns

### 1. Immutability After Storage

```python
structure = StructureData(...)
structure.store()

# ❌ Cannot modify stored structure
structure.properties.cell = ...  # AttributeError
structure.properties.sites[0].charge = ...  # TypeError
```

**Reason**: AiiDA Data nodes represent immutable calculation inputs/outputs.

### 2. Lazy Loading

```python
structure = orm.load_node(pk)
# Repository not accessed yet

positions = structure.properties.positions
# Now loads properties.npz and caches

positions2 = structure.properties.positions
# Returns cached array (no I/O)
```

### 3. Computed Properties

```python
# Defined once in models.py
@computed_field
@property
def cell_volume(self) -> float:
    return abs(np.linalg.det(self.cell))

# Available everywhere
model.cell_volume         # From Pydantic model
structure.properties.cell_volume  # From stored structure
```

### 4. Threshold-Based Equality

```python
site1 = Site(position=(0, 0, 0), kind_name='Fe')
site2 = Site(position=(1e-9, 0, 0), kind_name='Fe')
site1 == site2  # True (within position threshold)

# Thresholds defined in Site model
position_threshold = 1e-8
charge_threshold = 1e-4
```

## File Organization

```
src/aiida_atomistic/data/structure/
├── __init__.py
├── site.py           # Site model
├── kind.py           # Kind model
├── models.py         # Pydantic models
├── structure.py      # StructureData (immutable)
├── builder.py        # StructureBuilder (mutable)
├── getter_mixin.py   # Property access for stored structures
└── utils.py          # Helper functions
```

**Module Responsibilities:**

| Module | Purpose | Mutable? |
|--------|---------|----------|
| `site.py` | Individual site representation | Yes |
| `kind.py` | Kind metadata | Yes |
| `models.py` | Data validation, computed properties | No (Pydantic) |
| `structure.py` | Stored structure | No (AiiDA Data) |
| `builder.py` | Interactive construction | Yes |
| `getter_mixin.py` | Property access layer | No (read-only) |

## Extension Points

### Adding Properties

See [Adding Properties Guide](../dev_guides/dev_adding_properties.md) for details.

**Quick Summary:**

1. Add to `Site` model (optional)
2. Add to `StructureBaseModel` with metadata
3. Add statistics/queries as needed

### Custom Storage

By default, storage is determined in code. To add runtime storage choice:

1. Add parameter to `__init__`
2. Modify metadata before validation
3. Update `PropertyGetterMixin` to handle new locations

## Related Documentation

- [Properties Guide](properties.md) - All available properties
- [Immutability](immutability.md) - Mutable vs immutable classes
- [Storage Backends](storage_backends.md) - Database vs repository storage
- [Developer Guide: Adding Properties](../dev_guides/dev_adding_properties.md) - How to extend
- [How-to: Custom Properties](../how_to/define_custom.md) - Temporary properties
