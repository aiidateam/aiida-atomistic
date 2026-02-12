# Storage Backends

`aiida-atomistic` provides two different storage backends for structure data, each optimized for different use cases.

## Overview

| Backend | Storage Location | Best For | File |
|---------|------------------|----------|------|
| **Attribute-based** | Database attributes | Queryable metadata, small structures | `structuredata.py` |
| **Repository-based** | AiiDA repository (`.npz` files) | Large structures, array-heavy data | `structure.py` |

Both backends share the same API and pydantic models (`ImmutableStructureModel`, `MutableStructureModel`), making them interchangeable for most use cases.

## Attribute-Based Storage (Default)

**Class:** `StructureData`
**File:** `src/aiida_atomistic/data/structure/structuredata.py`

### How It Works

All structure data is stored in the AiiDA database attributes as JSON-serializable dictionaries:

```python
from aiida_atomistic.data.structure import StructureData

structure = StructureData(
    pbc=[True, True, True],
    cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    sites=[
        {'symbol': 'Si', 'position': [0, 0, 0]},
        {'symbol': 'Si', 'position': [1.5, 1.5, 1.5]}
    ]
)
structure.store()  # Stores everything in database attributes
```

### Advantages

- **Queryable**: All properties stored in the database can be queried using AiiDA's QueryBuilder
- **Simple**: Single storage location, no separate files to manage
- **Kinds compression**: Automatically compresses repeated site data using kinds

### When to Use

- Small to medium structures (< 1000 atoms)
- When you need to query structure properties frequently
- When database size is not a concern
- For most standard use cases

### Storage Format

```python
# Database attributes (simplified)
{
    "pbc": [true, true, true],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "kind_names": ["Si1", "Si1"],  # Compressed via kinds
    "symbols": ["Si"],
    "positions": [[[0, 0, 0], [1.5, 1.5, 1.5]]],  # Grouped by kind
    "tot_charge": 0.0,
    ...
}
```

## Repository-Based Storage

**Class:** `StructureData`
**File:** `src/aiida_atomistic/data/structure/structure.py`

### How It Works

Structure data is **intelligently split** between database attributes and repository files based on metadata:

- **Database attributes**: Queryable metadata (cell parameters, formulas, statistics)
- **Repository file**: Large numeric arrays (positions, charges, magnetic moments)

```python
from aiida_atomistic.data.structure import StructureData

structure = StructureData(
    pbc=[True, True, True],
    cell=[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    sites=[
        {'symbol': 'Si', 'position': [0, 0, 0], 'charge': 0.5},
        {'symbol': 'Si', 'position': [1.5, 1.5, 1.5], 'charge': 0.5}
    ]
)
structure.store()
# Stores: cell, pbc, formula → database (queryable)
#         positions, charges → properties.npz file (efficient)
```

### Advantages

- **Scalable**: Handles large structures with thousands of atoms efficiently
- **Efficient**: NumPy arrays compressed in `.npz` format
- **Smart splitting**: Automatically separates queryable metadata from bulk arrays
- **Flexible**: Metadata-driven storage decisions (see below)

### When to Use

- Large structures (> 1000 atoms)
- Array-heavy data (e.g., charge densities, magnetic moments for all atoms)
- When database bloat is a concern
- High-throughput workflows with many large structures

### Storage Format

**Database attributes (only queryable metadata):**
```python
{
    "pbc": [true, true, true],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "formula": "Si2",
    "cell_volume": 27.0,
    "dimensionality": 3,
    "is_alloy": false,
    "has_vacancies": false,
    "max_charge": 0.5,
    "min_charge": 0.5,
    ...
}
```

**Repository file (`properties.npz`):**
```python
{
    "positions": [[0, 0, 0], [1.5, 1.5, 1.5]],  # N×3 array
    "charges": [0.5, 0.5],                      # N array
    "masses": [28.085, 28.085],                 # N array
    "symbols": ["Si", "Si"],                    # list (stored as array)
    ...
}
```

## Metadata-Driven Storage Decisions

The repository backend uses **field metadata** to automatically determine where each property should be stored.

### Storage Metadata Keys

Each field in `models.py` has `json_schema_extra` metadata:

```python
# Example from models.py
class ImmutableStructureModel(StructureBaseModel):
    # Global property → database (queryable)
    cell: ArrayLike3x3 = Field(
        json_schema_extra={"store_in": "db", "property_type": "global"}
    )

    @computed_field(json_schema_extra={"store_in": "repository", "property_type": "computed"})
    @property
    def positions(self) -> np.ndarray:
        """Positions array → repository (large array)"""
        return np.array([site.position for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
    @property
    def formula(self) -> str:
        """Formula → database (queryable metadata)"""
        return self._compute_formula()
```

### Metadata Keys

| Key | Values | Purpose |
|-----|--------|---------|
| `store_in` | `"db"`, `"npz"`, `"repo"`, `"repository"`, `"attribute"`, `"attributes"` | Where to store the property |
| `property_type` | `"global"`, `"computed"`, `"internal"` | Classification of the property |
| `statistic` | `"max"`, `"min"` | Indicates a statistical field |
| `singular_form` | String (e.g., `"position"`) | **Required for site-array properties** - Maps plural property to singular site field |

:::{important}
**`singular_form` is critical for site-array properties!**

When a computed field represents an array of site-level values, you MUST specify how it maps back to the individual site property:

```python
@computed_field(
    json_schema_extra={
        "store_in": "repository",
        "property_type": "computed",
        "singular_form": "charge"  # ← REQUIRED
    }
)
@property
def charges(self) -> np.ndarray:
    """Array of charge values from all sites."""
    return np.array([site.charge for site in self.sites])
```

Without `singular_form`:
- ❌ Structure cannot be loaded from database
- ❌ Site reconstruction fails with `KeyError`
- ❌ Data becomes inaccessible after storing

Common mappings: `positions` → `"position"`, `charges` → `"charge"`, `symbols` → `"symbol"`
:::

### Storage Decision Logic

The `StructureData._get_storage_target()` method follows a simple decision process:

1. **Check field metadata** (`json_schema_extra["store_in"]`)
2. **Check computed field metadata** (`json_schema_extra["store_in"]`)
3. **Type-based fallback** (numeric arrays → repository, others → database)

```python
class StructureData:
    def _get_storage_target(self, prop_name, value):
        # 1. Check regular field metadata
        if prop_name in self._model.model_fields:
            metadata = self._model.model_fields[prop_name].json_schema_extra
            if metadata and "store_in" in metadata:
                store_in = metadata["store_in"]
                if store_in in {"npz", "repo", "repository"}:
                    return "repository"
                elif store_in in {"db", "attribute", "attributes"}:
                    return "attributes"

        # 2. Check computed field metadata
        if prop_name in self._model.model_computed_fields:
            computed_info = self._model.model_computed_fields[prop_name]
            metadata = getattr(computed_info, 'json_schema_extra', None)
            if metadata and "store_in" in metadata:
                store_in = metadata["store_in"]
                if store_in in {"npz", "repo", "repository"}:
                    return "repository"
                elif store_in in {"db", "attribute", "attributes"}:
                    return "attributes"

        # 3. Type-based fallback
        if self._is_numeric_array(value):
            return "repository"
        return "attributes"
```

All storage decisions are driven by the `store_in` metadata in `models.py`.
No hardcoded overrides needed!

### Property Classification

Properties are classified by `property_type`:

| Type | Description | Examples | Typical Storage |
|------|-------------|----------|-----------------|
| `global` | Structure-level properties | `pbc`, `cell`, `tot_charge` | Database |
| `computed` | Calculated properties | `positions`, `formula`, `cell_volume` | Mixed (see below) |
| `internal` | Internal representations | `sites` | Database |

### Storage by Property Type

**Stored in Database (`store_in="db"`):**

- **Queryable metadata** - Needed for searches:
  - `cell`, `pbc`, `tot_charge`, `tot_magnetization`
  - `cell_volume`, `dimensionality`, `formula`
  - `is_alloy`, `has_vacancies`
  - `kind_names`, `symbols` (for quick lookups)

- **Statistics** - For range queries:
  - `max_charge`, `min_charge`
  - `max_magmom`, `min_magmom`
  - `max_magnetization`, `min_magnetization`
  - `n_sites` (total number of atoms)

**Stored in Repository (`store_in="npz"`):**

- **Large numeric arrays**:
  - `positions` (N×3 array)
  - `masses` (N array)
  - `charges` (N array)
  - `magmoms` (N×3 array)
  - `magnetizations` (N array)
  - `weights` (list of tuples)

**Not Stored (reconstructed on-the-fly):**

- `kinds` - Reconstructed from `kind_names` and other stored properties
- `sites` (internal representation) - Rebuilt from stored arrays

## Loading Structures from Database

### How Repository-Based Loading Works

When you load a `StructureDataRepository` from the database, the system reconstructs the structure from both storage locations:

```python
loaded = orm.load_node(pk)
# 1. Loads database attributes: cell, pbc, formula, statistics, etc.
# 2. Loads repository file: properties.npz with arrays
# 3. Reconstructs sites from arrays using singular_form mappings
```

#### The `singular_form` Mapping

The `singular_form` metadata is **critical** for reconstructing sites from stored arrays:

**Storage (when saving):**
```python
structure = StructureDataRepository(
    sites=[
        {'symbol': 'H', 'position': [0,0,0], 'charge': 0.5},
        {'symbol': 'O', 'position': [0,0,1], 'charge': -1.0},
    ]
)
structure.store()

# Stores as arrays:
# - positions: [[0,0,0], [0,0,1]]  (in .npz)
# - charges: [0.5, -1.0]           (in .npz)
# - symbols: ['H', 'O']            (in DB)
```

**Loading (when retrieving):**
```python
loaded = orm.load_node(pk)

# System needs to know: positions → position, charges → charge, symbols → symbol
# Uses singular_form metadata from models.py:

@computed_field(json_schema_extra={"singular_form": "position", "store_in": "repository"})
def positions(self): ...

@computed_field(json_schema_extra={"singular_form": "charge", "store_in": "repository"})
def charges(self): ...

@computed_field(json_schema_extra={"singular_form": "symbol", "store_in": "db"})
def symbols(self): ...

# Reconstructs sites:
# sites[0] = {'position': [0,0,0], 'charge': 0.5, 'symbol': 'H'}
# sites[1] = {'position': [0,0,1], 'charge': -1.0, 'symbol': 'O'}
```

**Without `singular_form`:**
```python
# ❌ System doesn't know how to map 'charges' array back to site property
# Result: KeyError when trying to reconstruct sites
# Your data becomes inaccessible!
```

#### Complete Example

```python
# models.py - ALL site-array properties need singular_form
class ImmutableStructureModel(StructureBaseModel):
    @computed_field(
        json_schema_extra={
            "store_in": "repository",
            "property_type": "computed",
            "singular_form": "position"  # positions → position
        }
    )
    @property
    def positions(self) -> np.ndarray:
        return np.array([site.position for site in self.sites])

    @computed_field(
        json_schema_extra={
            "store_in": "repository",
            "property_type": "computed",
            "singular_form": "charge"  # charges → charge
        }
    )
    @property
    def charges(self) -> np.ndarray:
        return np.array([site.charge for site in self.sites])

    # Statistics DON'T need singular_form (not site-level)
    @computed_field(
        json_schema_extra={
            "store_in": "db",
            "property_type": "computed",
            "statistic": "max"
        }
    )
    @property
    def max_charge(self) -> float:
        return float(np.max(self.charges))
```

## Querying with Different Backends

### Attribute-Based Storage

All properties are queryable:

```python
from aiida.orm import QueryBuilder
from aiida_atomistic.data.structure import StructureData

qb = QueryBuilder()
qb.append(
    StructureData,
    filters={
        'attributes.formula': 'Si2',
        'attributes.cell_volume': {'<': 30.0}
    }
)
```

### Repository-Based Storage

**IMPORTANT**: Only database-stored properties are queryable. Properties in `.npz` files cannot be queried.

#### Checking Queryable Properties

Use `get_queryable_properties()` or `print_queryable_properties()` to see what can be queried:

```python
from aiida_atomistic.data.structure.structure import StructureDataRepository

# Get queryable properties programmatically
props = StructureDataRepository.get_queryable_properties()
print(props['queryable'])
# ['cell', 'cell_volume', 'custom', 'dimensionality', 'formula',
#  'has_vacancies', 'is_alloy', 'kind_names', 'max_charge', ...]

print(props['not_queryable'])
# ['charges', 'kinds', 'magmoms', 'magnetizations', 'masses', 'positions', 'weights']

# Or print a formatted overview
StructureDataRepository.print_queryable_properties()
```

Output:
```
═══════════════════════════════════════════════════════════════
Queryable Properties for StructureDataRepository
═══════════════════════════════════════════════════════════════

✓ QUERYABLE (stored in database attributes):
  • cell
  • cell_volume
  • custom
  • dimensionality
  • formula
  • has_vacancies
  • is_alloy
  • kind_names
  • max_charge
  • max_magmom
  • max_magnetization
  • min_charge
  • min_magmom
  • min_magnetization
  • n_sites
  • pbc
  • symbols
  • tot_charge
  • tot_magnetization

✗ NOT QUERYABLE (stored in .npz repository):
  • charges
  • magmoms
  • magnetizations
  • masses
  • positions
  • weights

⚠ NOT QUERYABLE (computed on-the-fly, not stored):
  • kinds
```

#### Query Example

```python
from aiida.orm import QueryBuilder
from aiida_atomistic.data.structure.structure import StructureDataRepository

qb = QueryBuilder()
qb.append(
    StructureDataRepository,
    filters={
        'attributes.formula': 'Si2',           # ✓ Queryable (in DB)
        'attributes.cell_volume': {'<': 30.0}, # ✓ Queryable (in DB)
        'attributes.max_charge': {'>': 0.5},   # ✓ Queryable (in DB)
        # 'attributes.positions': ...          # ✗ Not queryable (in .npz)
    }
)
```

### Query Example: Finding Structures

```python
# Find all silicon structures with volume < 30 Å³ and high charges
qb = QueryBuilder()
qb.append(
    StructureDataRepository,
    filters={
        'attributes.formula': {'like': 'Si%'},
        'attributes.cell_volume': {'<': 30.0},
        'attributes.max_charge': {'>': 0.5},
    },
    project=['uuid', 'attributes.formula', 'attributes.cell_volume']
)

for uuid, formula, volume in qb.all():
    # Load full structure (including arrays from .npz)
    structure = load_node(uuid)
    positions = structure.positions  # Loaded from properties.npz
    charges = structure.charges      # Loaded from properties.npz
```

:::{tip}
**Query Statistics Instead of Arrays**

Since array properties are not queryable, use the statistical fields:
- Instead of querying individual charges, use `max_charge`, `min_charge`
- Instead of querying individual magmoms, use `max_magmom`, `min_magmom`
- Use `n_sites` to filter by structure size
- Use `formula`, `is_alloy`, `has_vacancies` for composition queries
:::

## Adding Custom Storage Logic

### Method 1: Metadata in Models (Recommended)

The recommended way is to update `models.py` with proper metadata:

```python
class ImmutableStructureModel(StructureBaseModel):
    my_property: Optional[np.ndarray] = Field(
        default=None,
        json_schema_extra={
            "store_in": "repository",           # Store in repository
            "property_type": "global",
            "description": "My custom array property"
        }
    )

    @computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
    @property
    def my_queryable_stat(self) -> float:
        """Store in database for querying."""
        if self.my_property is None:
            return None
        return float(np.max(self.my_property))
```

This approach:
- ✅ Self-documenting (metadata lives with the field definition)
- ✅ No subclassing needed
- ✅ Works for both regular and computed fields
- ✅ Centralized in models.py

### Method 2: Override Decision Method

For complex conditional logic based on runtime values:

```python
class MyCustomStructure(StructureDataRepository):
    def _get_storage_target(self, prop_name, value):
        # Custom logic based on property name or value
        if prop_name.startswith('large_'):
            return 'repository'
        if prop_name.endswith('_metadata'):
            return 'attributes'

        # For very large arrays, force repository storage
        if isinstance(value, np.ndarray) and value.nbytes > 1_000_000:  # > 1MB
            return 'repository'

        # Fall back to default logic
        return super()._get_storage_target(prop_name, value)
```

## Performance Considerations

### Attribute-Based Storage

**Pros:**
- Fast queries (everything in database index)
- Simple mental model
- No file I/O overhead

**Cons:**
- Database bloat for large structures
- Slower database operations with many large structures
- Memory overhead in PostgreSQL

### Repository-Based Storage

**Pros:**
- Constant database size regardless of structure size
- Fast queries on metadata (small database)
- Efficient compression (`.npz` files)
- Scales to very large structures

**Cons:**
- Slight overhead loading full structure (need to read `.npz`)
- Cannot query array contents directly
- Two-step access pattern (query metadata, then load arrays)

### Recommendations

| Structure Size | Recommended Backend | Reason |
|---------------|---------------------|--------|
| < 100 atoms | Attribute-based | Simple, fast, no overhead |
| 100-1000 atoms | Either | Depends on query patterns |
| > 1000 atoms | Repository-based | Prevents database bloat |
| High-throughput | Repository-based | Better scalability |
| Query-intensive | Attribute-based | All data queryable |

## Migration Between Backends

### Attribute → Repository

```python
from aiida_atomistic.data.structure import StructureData
from aiida_atomistic.data.structure.structure import StructureDataRepository

# Load existing attribute-based structure
old_structure = load_node('uuid-here')

# Create repository-based version
new_structure = StructureDataRepository(**old_structure.properties.model_dump())
new_structure.store()
```

### Repository → Attribute

```python
from aiida_atomistic.data.structure.structure import StructureDataRepository
from aiida_atomistic.data.structure import StructureData

# Load existing repository-based structure
old_structure = load_node('uuid-here')

# Create attribute-based version
new_structure = StructureData(**old_structure.properties.model_dump())
new_structure.store()
```

## Technical Details

### NPZ File Format

Repository storage uses NumPy's `.npz` format:

```python
import numpy as np

# What's stored in properties.npz
np.savez_compressed(
    'properties.npz',
    positions=positions_array,  # float64, shape (N, 3)
    charges=charges_array,      # float64, shape (N,)
    masses=masses_array,        # float64, shape (N,)
    symbols=symbols_list,       # object array of strings
    ...
)
```

### Caching

Repository arrays are cached after first load:

```python
structure = load_node('uuid')
positions1 = structure.positions  # Loads from .npz, caches result
positions2 = structure.positions  # Returns cached array (no file I/O)
```

Cache is stored in `self._npz_cache` and cleared on node reload.

### File Location

Repository files are stored in AiiDA's standard repository structure:

```
~/.aiida/repository/<profile>/
  └── node/
      └── <first_2_uuid_chars>/
          └── <next_2_uuid_chars>/
              └── <uuid>/
                  └── properties.npz
```

Managed automatically by AiiDA - no manual file handling needed.
