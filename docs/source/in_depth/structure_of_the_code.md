# Code Structure and Architecture

This page provides a detailed overview of the `aiida-atomistic` code architecture, explaining the design decisions, class hierarchies, and how different components work together.

## Design Philosophy

The `aiida-atomistic` package follows a **site-centric architecture** where:

- **Sites are fundamental units**: Each atomic site contains all its properties (position, symbol, charge, magnetic moment, etc.)
- **Arrays are computed fields**: Properties like `positions`, `charges`, `magmoms` are automatically generated from individual sites
- **Kinds are derived**: Groups of sites with identical properties (except position) are automatically detected and grouped
- **Dual mutability system**: Separate mutable and immutable classes provide flexibility while maintaining AiiDA compatibility

This design makes it easy to add/modify individual atoms while maintaining data integrity and enabling efficient storage.

## Class Hierarchy

### Overview

```
BaseModel (Pydantic)
├── Site
│   ├── FrozenSite (immutable variant)
│   └── Kind (extends Site with position array)
│
├── StructureBaseModel
│   ├── MutableStructureModel
│   └── ImmutableStructureModel
│
└── Data (AiiDA)
    ├── StructureData (immutable, database-storable)
    │   └── properties: ImmutableStructureModel
    └── StructureBuilder (mutable, for building/modifying)
        └── properties: MutableStructureModel
```

### Two Parallel Paths

1. **AiiDA Path**: `StructureData` (immutable) → stored in database, provenance tracked
2. **Python Path**: `StructureBuilder` (mutable) → for building and modifying structures

You can easily convert between them:
```python
# Immutable → Mutable
builder = structure_data.get_value()

# Mutable → Immutable
structure_data = StructureData.from_builder(builder)
```

## Core Components

### 1. Site Model (`site.py`)

The `Site` class represents a single atomic site with all its properties.

**Key Fields:**
```python
class Site(BaseModel):
    symbol: Union[str, List[str]]  # Element symbol(s)
    position: np.ndarray           # 3D position [x, y, z]
    mass: Optional[float]          # Atomic mass
    charge: Optional[float]        # Charge
    magmom: Optional[np.ndarray]   # Magnetic moment vector [mx, my, mz]
    magnetization: Optional[float] # Scalar magnetization
    weight: Optional[Tuple[float, ...]]  # For alloys/vacancies
    kind_name: Optional[str]       # Kind identifier
```

**Special Features:**

- **Alloy support**: Multiple symbols with weights (e.g., `["Si", "Ge"]` with `weights=(0.5, 0.5)`)
- **Vacancy support**: Weights summing to < 1 indicate vacancies
- **Automatic mass**: Calculated from element symbols if not provided
- **Validation**: Ensures positions are 3D, symbols are valid elements and so on

**Immutable Variant:**

`FrozenSite` is an immutable version where all fields are frozen and cannot be modified after creation.

### 2. Structure Model (`models.py`)

The `StructureBaseModel` represents a complete atomic structure.

**Global Properties:**
```python
class StructureBaseModel(BaseModel):
    pbc: list[bool]              # Periodic boundary conditions [x, y, z]
    cell: np.ndarray             # 3×3 lattice vectors matrix
    sites: list[Site]            # List of atomic sites
    tot_magnetization: Optional[float]
    tot_charge: Optional[float]
    hubbard: Optional[Hubbard]   # Hubbard parameters
    custom: Optional[dict]       # Custom properties
```

**Computed Fields** (automatically calculated from sites):

- `positions` → Array of all site positions
- `symbols` → List of chemical symbols
- `masses`, `charges`, `magmoms`, `magnetizations`, `weights` → Property arrays
- `kind_names` → List mapping each site to its kind
- `kinds` → List of `Kind` objects (grouped sites)
- `formula` → Chemical formula
- `cell_volume` → Unit cell volume
- `dimensionality` → 0D/1D/2D/3D classification
- `is_alloy` → Whether structure contains alloys
- `has_vacancies` → Whether structure has vacancies

**Two Variants:**

1. **MutableStructureModel**: `_mutable = True`, sites can be modified
2. **ImmutableStructureModel**: `_mutable = False`, all properties frozen

### 3. The Kinds System

**What are Kinds?**

A "kind" represents a group of sites that share ALL properties except position. For example, in a water molecule, both H atoms have the same properties (mass, charge, etc.) but different positions, so they belong to the same kind.

**Why Kinds?**

- **Storage efficiency**: Store one kind definition + N positions instead of N identical site definitions
- **Computational efficiency**: Perform operations on groups of identical atoms
- **Physical meaning**: Distinguish chemically identical but structurally distinct atoms (e.g., bulk vs. surface atoms)

**Automatic Detection:**

The `generate_kinds()` method automatically detects kinds by grouping sites with identical properties:

```python
builder = StructureBuilder(sites=[...])
builder.generate_kinds()  # Automatically assigns kind_names
```

**Kind Model:**

```python
class Kind(Site):
    positions: np.ndarray      # All positions for this kind [(x1,y1,z1), (x2,y2,z2), ...]
    site_indices: List[int]    # Indices of sites belonging to this kind
```

**Example:**

```python
# Input: 3 sites
sites = [
    {"symbol": "H", "position": [0, 0, 0], "charge": 0.4},
    {"symbol": "H", "position": [1, 0, 0], "charge": 0.4},  # Same as site 0
    {"symbol": "O", "position": [0, 1, 0], "charge": -0.8}
]

# After kind detection → 2 kinds:
# Kind 1: symbol="H", charge=0.4, positions=[[0,0,0], [1,0,0]], site_indices=[0,1]
# Kind 2: symbol="O", charge=-0.8, positions=[[0,1,0]], site_indices=[2]
```

### 4. Validation System

The package implements multi-layer validation to ensure data integrity:

**Layer 1: Pydantic Field Validators**
- Type checking (e.g., `position` must be array-like)
- Shape validation (e.g., `cell` must be 3×3)
- Value constraints (e.g., `mass` > 0)

**Layer 2: Pydantic Model Validators**
- `check_minimal_requirements`: Validates structure completeness
- `check_is_alloy`: Detects and configures alloy sites
- Mutual exclusivity checks (e.g., can't have both `magmom` and `magnetization`)

**Layer 3: Custom Validation Methods**
- `validate_kinds()`: Ensures all sites with the same `kind_name` have identical properties
- `_check_valid_sites()`: Checks that sites aren't too close together (prevents unphysical structures)

**Layer 4: Setter Validation**
- Length matching (e.g., `charges` array must match number of sites)
- Type coercion
- Automatic updates to dependent fields

**Configurable Tolerances:**

When comparing properties for kind validation, the following tolerances are used:

```python
_DEFAULT_THRESHOLDS = {
    "charges": 0.1,
    "masses": 1e-4,
    "magmoms": 1e-4,
}
```

## Immutability Implementation

AiiDA requires stored data nodes to be immutable. The package implements this through multiple protection layers:

### Layer 1: Pydantic Configuration
```python
class ImmutableStructureModel(StructureBaseModel):
    model_config = ConfigDict(frozen=True)  # Pydantic-level immutability
```

### Layer 2: Custom `__setattr__`
```python
def __setattr__(self, key, value):
    if key in self.model_fields:
        raise ValueError("StructureData is immutable. Use get_value() for mutable copy.")
    super().__setattr__(key, value)
```

### Layer 3: Frozen NumPy Arrays
```python
@field_validator('position', 'magmom', mode='before')
def ensure_numpy_array(cls, v):
    array_v = np.asarray(v)
    array_v.flags.writeable = False  # Make array read-only
    return array_v
```

### Layer 4: FrozenList and FrozenSite
```python
class FrozenList(list):
    def __setitem__(self, index, value):
        raise ValueError("This list is immutable. Use setter methods on mutable copy.")
```

### Layer 5: Nested Freezing

All nested structures (lists of sites, dictionaries, etc.) are recursively frozen.

### Working with Immutable Structures

```python
# Get immutable structure from database
structure = load_node(pk)

# Cannot modify directly
structure.properties.pbc[0] = False  # ❌ Raises ValueError

# Get mutable copy for modifications
builder = structure.get_value()
builder.set_pbc([True, True, False])  # ✅ Works
builder.sites[0].charge = -1.0        # ✅ Works

# Convert back to immutable for storage
new_structure = StructureData.from_builder(builder)
new_structure.store()
```

## Storage Architecture

AiiDA-atomistic provides two storage backends, each optimized for different use cases:

### 1. Attribute-Based Storage (Default)

**Class:** `StructureData`
**Storage:** All data in AiiDA database attributes

All structure properties are stored as JSON-serializable data in the database. This enables full queryability but can lead to database bloat for large structures.

```python
# Without kinds (site-based storage)
{
    "pbc": [true, true, true],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "positions": [[0,0,0], [1,0,0], [0,1,0]],
    "symbols": ["H", "H", "O"],
    "charges": [0.4, 0.4, -0.8],
    ...
}
```

```python
# With kinds (compressed storage)
{
    "pbc": [true, true, true],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "kind_names": ["H1", "H1", "O1"],
    "site_indices": [[0, 1], [2]],
    "positions": [[[0,0,0], [1,0,0]], [[0,1,0]]],  # Grouped by kind
    "symbols": ["H", "O"],      # One per kind
    "charges": [0.4, -0.8],     # One per kind
    ...
}
```

**Compression Benefits:**

For structures with many identical atoms (e.g., 1000 water molecules = 3000 atoms but only 2 kinds), kinds-based storage significantly reduces database size.

### 2. Repository-Based Storage

**Class:** `StructureDataRepository`
**Storage:** Metadata in database attributes, arrays in `.npz` files

Data is intelligently split based on field metadata:
- **Database attributes**: Queryable properties (cell, formula, statistics)
- **Repository file**: Large numeric arrays (positions, charges, magmoms)

```python
# Database attributes (queryable metadata only)
{
    "pbc": [true, true, true],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "formula": "H2O",
    "cell_volume": 27.0,
    "n_sites": 3,
    "max_charge": 0.4,
    "min_charge": -0.8,
    ...
}

# Repository file: properties.npz (compressed arrays)
{
    "positions": [[0,0,0], [1,0,0], [0,1,0]],  # NumPy array
    "charges": [0.4, 0.4, -0.8],                # NumPy array
    "masses": [1.008, 1.008, 15.999],           # NumPy array
    ...
}
```

**When to use which:**
- **Attribute-based**: Small structures (< 1000 atoms), query-intensive workflows
- **Repository-based**: Large structures (> 1000 atoms), high-throughput workflows

See the [Storage Backends](storage_backends.md) documentation for detailed comparison and migration guide.

### Metadata-Driven Storage Decisions

The repository backend uses field metadata to automatically determine storage location:

```python
# From models.py - metadata controls storage
class ImmutableStructureModel(StructureBaseModel):
    # Queryable → database
    cell: ArrayLike3x3 = Field(
        json_schema_extra={"store_in": "db", "property_type": "global"}
    )

    @computed_field(json_schema_extra={"store_in": "repository", "property_type": "computed"})
    @property
    def positions(self) -> np.ndarray:
        """Large array → repository"""
        return np.array([site.position for site in self.sites])

    @computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
    @property
    def formula(self) -> str:
        """Metadata → database (queryable)"""
        return self._compute_formula()
```

Storage decision hierarchy:
1. Explicit overrides (`_storage_overrides` dict)
2. Field metadata (`json_schema_extra["store_in"]`)
3. Type-based fallback (numeric arrays → repository)

### Loading Process

When loading from the database, data is automatically reconstructed:

**Attribute-based storage:**
1. Check if `kind_names` exists in attributes
2. If yes: decompress kinds → sites using `rebuild_site_lists_from_kind_lists()`
3. Build `Site` objects from expanded properties
4. Create `ImmutableStructureModel` with reconstructed sites

**Repository-based storage:**
1. Load queryable metadata from database attributes
2. Load arrays from `properties.npz` file (cached after first access)
3. Reconstruct full structure in memory
4. Create `ImmutableStructureModel` combining both sources

**Key Insight**: Storage is optimized (kinds-based or split repo/db), but the in-memory representation is always site-based for ease of use.

## Getter and Setter Mixins

### GetterMixin (`getter_mixin.py`)

Available for both `StructureData` and `StructureBuilder`, provides:

**Convenience Properties:**
```python
structure.cell           # Access cell directly
structure.pbc            # Access PBC
structure.sites          # Access sites list
structure.kinds          # Access kinds (if detected)
structure.formula        # Get chemical formula
```

**Conversion Methods:**
```python
atoms = structure.to_ase()           # → ASE Atoms
pmg_struct = structure.to_pymatgen() # → pymatgen Structure
structure.to_file('output.cif')     # Write to file
```

**Factory Methods:**
```python
structure = StructureData.from_ase(atoms)
structure = StructureData.from_pymatgen(pmg_struct)
structure = StructureData.from_file('input.cif')
```

**Query Methods:**
```python
structure.get_supported_properties()  # All available properties
structure.get_defined_properties()    # Properties actually set
```

**Validation:**
```python
structure.validate_kinds()  # Check kinds consistency
```

**Serialization:**
```python
data_dict = structure.to_dict()
dump = structure.properties.model_dump()
```

### SetterMixin (`setter_mixin.py`)

Only available for `StructureBuilder` (mutable structures), provides modification methods:

**Setting Properties:**
```python
builder.set_cell([[3, 0, 0], [0, 3, 0], [0, 0, 3]])
builder.set_pbc([True, True, False])
builder.set_charges([0.4, 0.4, -0.8])
builder.set_magmoms([[0, 0, 1], [0, 0, 1], [0, 0, 0]])
```

**Adding/Removing Atoms:**
```python
builder.append_atom(symbol='H', position=[0, 0, 0], charge=0.4)
builder.remove_sites([0, 2])  # Remove sites by index
```

**Removing Properties:**
```python
builder.remove_charges()   # Remove all charges
builder.remove_magmoms()   # Remove all magnetic moments
```

**Updating Sites:**
```python
builder.update_sites(site_indices=[0, 1], charge=0.5)  # Update specific sites
```

**Kind Generation:**
```python
builder.generate_kinds(tolerance={'charges': 0.1})  # Auto-detect kinds
```

## Performance Considerations

### Computational Complexity

- **Kind detection**: O(N) where N = number of sites
- **Site validation**: O(N²) for pairwise distance checking (vectorized)
- **Computed fields**: Cached after first access (O(1) subsequent access)
- **Kinds compression/decompression**: O(N × K) where K = number of kinds

### Optimization Features

**Automatic Caching:**
All `@computed_field` properties are automatically cached by Pydantic:
```python
positions = structure.properties.positions  # Computed once
positions2 = structure.properties.positions # Retrieved from cache
```

**Efficient Copying:**
The `efficient_copy()` utility selectively copies only mutable parts, avoiding deep copy overhead.

**Vectorized Operations:**
NumPy operations are used throughout for array manipulations (e.g., distance calculations).

### Best Practices for Large Structures

For structures with >10,000 atoms:
- Use kinds compression (automatically enabled when kinds are detected)
- Consider disabling `_check_valid_sites` validation if sites are trusted
- Use batch operations instead of modifying sites one-by-one

## String Representations

The package provides informative `__repr__` methods for debugging and inspection:

### Site Representation
```python
site = Site(symbol='Fe', position=[0, 0, 0], charge=1.0, magnetization=2.5)
print(site)
# Output: Site(Fe @ [0.000, 0.000, 0.000], charge=1.00, mag=2.50)
```

### Structure Representation
```python
structure = StructureData(...)
print(structure.properties)
# Output:
#  | formula: H2O, sites: 3, dimensionality: 3D, V=27.00 A^3 | Sites: [
#   Site(H @ [0.000, 0.000, 0.000], kind=H1)
#   Site(H @ [1.000, 0.000, 0.000], kind=H1)
#   Site(O @ [0.500, 0.866, 0.000], kind=O1)
#  ]
```

## Summary

The `aiida-atomistic` architecture provides:

✅ **Flexible**: Site-centric design makes modifications intuitive
✅ **Safe**: Multiple immutability layers protect stored data
✅ **Efficient**: Kinds compression and computed field caching optimize performance
✅ **Compatible**: Seamless integration with ASE, pymatgen, and AiiDA
✅ **Extensible**: Clear patterns for adding new properties
✅ **Validated**: Multi-layer validation ensures data integrity

This design balances ease of use with the strict requirements of scientific data management and provenance tracking in AiiDA.
