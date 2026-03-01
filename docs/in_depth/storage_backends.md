# Storage Backends

This document explains how `aiida-atomistic` stores structure data in AiiDA's database and repository.

## Overview

`StructureData` stores properties in two locations:

1. **Database attributes**: Queryable metadata (formulas, statistics, small arrays)
2. **Repository files**: Large numeric arrays (positions, charges, magnetic moments)

!!! note
    **Storage location is determined at the code level, not at runtime.**

    When you create a `StructureData`, the storage location for each property is already defined in the source code via metadata in `models.py`. You cannot choose where properties are stored when creating structures.

    **Developers** can decide storage locations when adding new properties by setting metadata in `models.py`.

## How Storage Works

Each property in `models.py` has metadata that determines its storage location:

```python
# From models.py - storage is defined here
class StructureBaseModel(BaseModel):
    # This property goes to database
    cell: ArrayLike3x3 = Field(
        json_schema_extra={"store_in": "db"}
    )

    # This array goes to repository
    @computed_field(json_schema_extra={"store_in": "repository", "singular_form": "position"})
    @property
    def positions(self) -> np.ndarray:
        return np.array([site.position for site in self.sites])
```

When you store a structure, the system uses these metadata settings automatically:

```python
structure = StructureData(
    cell=[[3, 0, 0], [0, 3, 0], [0, 0, 3]],
    pbc=[True, True, True],
    sites=[...]
)
structure.store()
# cell → database (as defined by store_in="db")
# positions → repository (as defined by store_in="repository")
```

## What Gets Stored Where

**Database Attributes** (queryable):

- Global properties: `cell`, `pbc`, `tot_charge`, `tot_magnetization`
- Computed metadata: `formula`, `cell_volume`, `dimensionality`, `n_sites`
- Composition flags: `is_alloy`, `has_vacancies`
- Statistics: `max_charge`, `min_charge`, `max_magmom`, `min_magmom`, etc.
- Small arrays: `symbols`, `kind_names`

**Repository Files** (`properties.npz`):

- Large numeric arrays: `positions`, `masses`, `charges`, `magmoms`, `magnetizations`, `weights`

**Not Stored** (reconstructed on access):

- `kinds` - Rebuilt from stored properties
- `sites` (internal) - Rebuilt from stored arrays

## Storage Metadata

### The `store_in` Key

Each field uses `json_schema_extra` metadata with a `store_in` key:

| `store_in` Value | Storage Location |
|------------------|------------------|
| `"db"`, `"attribute"`, `"attributes"` | Database attributes |
| `"repository"`, `"repo"`, `"npz"` | Repository `.npz` file |

### The `singular_form` Key (Required for Array Properties)

For computed array properties from sites, `singular_form` maps the array back to individual site fields:

```python
@computed_field(
    json_schema_extra={
        "store_in": "repository",
        "singular_form": "charge"  # Maps 'charges' array → 'charge' site property
    }
)
@property
def charges(self) -> np.ndarray:
    return np.array([site.charge for site in self.sites])
```

!!! note
    Without `singular_form`, the system cannot reconstruct sites when loading from the database, causing `KeyError` and making data inaccessible.


## Querying Structures

### Database Properties are Queryable

```python
from aiida.orm import QueryBuilder
from aiida_atomistic.data.structure import StructureData

qb = QueryBuilder()
qb.append(
    StructureData,
    filters={
        'attributes.formula': 'H2O',           # ✓ Queryable
        'attributes.cell_volume': {'<': 30},   # ✓ Queryable
        'attributes.max_charge': {'>': 1.0},   # ✓ Queryable
    }
)
```

### Repository Properties are NOT Queryable

Arrays in `.npz` files cannot be queried:

```python
qb.append(
    StructureData,
    filters={
        'attributes.positions': ...  # ✗ Not queryable - stored in .npz
        'attributes.charges': ...    # ✗ Not queryable - stored in .npz
    }
)
```

**Solution**: Query statistical properties stored in the database:

```python
qb.append(
    StructureData,
    filters={
        'attributes.max_charge': {'>': 1.0, '<=': 2.0},  # ✓ Works
        'attributes.n_sites': {'>': 10},                  # ✓ Works
    }
)
```

## Adding New Properties (Developer Guide)

When adding properties to `aiida-atomistic`, you decide where they're stored.

### Step 1: Add Site Property

In `site.py`:

```python
class Site(BaseModel):
    my_property: t.Optional[float] = Field(
        default=None,
        json_schema_extra={"threshold": 1e-4, "default": 0.0}
    )
```

### Step 2: Add Array Property with Storage Metadata

In `models.py`:

```python
@computed_field(
    json_schema_extra={
        "store_in": "repository",      # ← Choose storage location
        "singular_form": "my_property" # ← Map array to site field
    }
)
@property
def my_properties(self) -> np.ndarray:
    """Array of my_property from all sites."""
    if all(site.my_property is None for site in self.sites):
        return None
    return np.array([
        site.my_property if site.my_property is not None
        else Site.get_default_values()['my_property']
        for site in self.sites
    ])
```

### Step 3: Add Statistics (Optional, for Querying)

```python
@computed_field(
    json_schema_extra={
        "store_in": "db",  # ← Store in database for querying
        "statistic": "max"
    }
)
@property
def max_my_property(self) -> t.Optional[float]:
    if self.my_properties is None:
        return None
    return float(np.max(self.my_properties))
```

### Choosing Storage Location

**Store in Database (`"db"`)** when:

- Property is small (strings, numbers, flags)
- You need to query by this property
- It's metadata for filtering/searching

**Store in Repository (`"repository"`)** when:

- Property is a large array
- You don't need to query array contents
- Storage efficiency matters

**Example Guidelines:**

| Property Type | Size | Queryable? | Store In |
|--------------|------|------------|----------|
| Formula | String | Yes | Database |
| Cell volume | Float | Yes | Database |
| Statistics (max/min) | Float | Yes | Database |
| Positions array | N×3 floats | No | Repository |
| Charges array | N floats | No | Repository |

## Performance Considerations

**Database Storage:**

- ✓ Fast queries - everything indexed
- ✗ Database grows with structure size

**Repository Storage:**

- ✓ Database stays small
- ✓ Efficient for large structures
- ✗ Cannot query array contents

**Recommendations:**

| Structure Size | Notes |
|---------------|-------|
| < 100 atoms | Database size usually fine |
| > 1000 atoms | Repository prevents database bloat |
| High-throughput | Repository scales better |

## Technical Details

### Storage Format

Repository uses NumPy's compressed `.npz` format:

```python
# What's in properties.npz
{
    'positions': np.array([[0,0,0], [1,1,1]]),  # N×3 float64
    'charges': np.array([1.0, -1.0]),            # N float64
    'masses': np.array([1.008, 15.999])          # N float64
}
```

### Caching

Arrays are cached after first load to avoid repeated file I/O:

```python
structure = orm.load_node(pk)
pos1 = structure.properties.positions  # Loads from .npz, caches
pos2 = structure.properties.positions  # Returns cached (no I/O)
```
