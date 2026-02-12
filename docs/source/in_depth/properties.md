## Property Types

Properties in aiida-atomistic fall into three categories:

### 1. Global Properties

Properties that apply to the entire structure (not per-site):

- `pbc` (periodic boundary conditions)
- `cell` (lattice vectors)
- `tot_charge` (total charge of the structure)
- `tot_magnetization` (total magnetization of the structure)
- `hubbard` (Hubbard parameters - global because it contains site indices for U and V parameters)

:::{note}
`hubbard` is a global property because Hubbard parameters reference site indices (e.g., for on-site U or inter-site V). For example, V parameters involve pairs of site indices, making it inherently a structure-level property rather than a per-site property.
:::

### 2. Site Properties

Properties defined per atomic site in the `Site` model. These are the fundamental properties stored for each site:

**Individual site properties** (accessed per site):
- `symbol` (chemical symbol, singular)
- `position` (atomic coordinates, 3D vector)
- `mass` (atomic mass, scalar)
- `charge` (atomic charge, scalar)
- `magmom` (magnetic moment vector, 3D) - **mutually exclusive with `magnetization`**
- `magnetization` (scalar magnetization) - **mutually exclusive with `magmom`**
- `kind_name` (kind identifier, string)
- `weight` (for alloys/vacancies, tuple)

**Computed array properties** (accessed for all sites at once):
- `symbols` (all chemical symbols as list)
- `positions` (all atomic coordinates as N×3 array)
- `masses` (all atomic masses as N array)
- `charges` (all atomic charges as N array)
- `magmoms` (all magnetic moment vectors as N×3 array)
- `magnetizations` (all scalar magnetizations as N array)
- `kind_names` (all kind identifiers as list)
- `weights` (all alloy/vacancy weights as list of tuples)

:::{note}
Computed array properties (plural names) aggregate the individual site properties (singular names) from all sites. For example:
- `site.charge` → single scalar value for one site
- `structure.properties.charges` → numpy array of all charges
:::

:::{warning}
**Mutually Exclusive Magnetic Properties:**

For each site, you must choose **either** `magmom` **or** `magnetization`, but not both:

- **`magmom`**: Use for non-collinear magnetism (3D vector `[x, y, z]`)
- **`magnetization`**: Use for collinear magnetism (scalar value)

Setting both on the same site will cause validation errors. See the [Magnetic Structures guide](../how_to/magnetic_structures.md) for details.
:::

### 3. Computed Properties

Properties calculated from other properties. Some are stored (for querying), others computed on-the-fly:

**Queryable computed properties** (stored in database attributes):
- `cell_volume` (calculated from `cell`)
- `dimensionality` (calculated from `pbc` and `cell`)
- `formula` (calculated from `symbols`)
- `is_alloy` (whether structure contains alloys)
- `has_vacancies` (whether structure contains vacancies)
- `n_sites` (total number of sites)

**Statistical properties** (stored in database for range queries):
- `max_charge`, `min_charge` (maximum and minimum charge values)
- `max_magmom`, `min_magmom` (maximum and minimum magnetic moment magnitudes)
- `max_magnetization`, `min_magnetization` (maximum and minimum magnetization values)

**Reconstructed properties** (not stored, computed on-the-fly):
- `kinds` (grouped site information based on properties)
- `kind_names`, `symbols` (when not using repository storage)
- the computed array properties (`positions`, `charges`, etc.)

These properties are mainly useful for [querying `StructureData` objects](../how_to/query.md).

:::{note}
**Storage Backend Differences:**

The storage location of properties depends on the backend used:
- **Attribute-based storage** (`StructureData`): Most properties stored in database attributes
- **Repository-based storage** (`StructureDataRepository`): Arrays stored in `.npz` files, queryable metadata in database

See [Storage Backends](storage_backends.md) for details.
:::

## Property Formats

### Individual Site Properties (Singular)

These are the actual fields stored in each `Site` object:

| Property | Format | Example |
|----------|--------|---------|
| `symbol` | `str` or `list[str]` | `'Cu'` or `['Cu', 'Zn']` (for alloys) |
| `position` | `list[float]` (length 3) | `[0, 0, 0]` |
| `mass` | `float` | `63.546` |
| `charge` | `float` | `1.0` |
| `magmom` | `list[float]` (length 3) | `[0, 0, 2.2]` ⚠️ *mutually exclusive with `magnetization`* |
| `magnetization` | `float` | `2.2` ⚠️ *mutually exclusive with `magmom`* |
| `kind_name` | `str` | `'Cu1'` |
| `weight` | `tuple[float]` | `(0.7, 0.3)` (for alloys) |

### Computed Array Properties (Plural)

These are computed fields that aggregate all sites' properties into arrays:

| Property | Type | Format | Example |
|----------|------|--------|---------|
| `symbols` | Computed | `list[str]` | `['Cu', 'Zn', 'Cu']` |
| `positions` | Computed | `np.ndarray` (N×3) | `[[0, 0, 0], [1.5, 1.5, 1.5]]` |
| `masses` | Computed | `np.ndarray` (N,) | `[63.546, 65.38]` |
| `charges` | Computed | `np.ndarray` (N,) | `[1.0, 2.0]` |
| `magmoms` | Computed | `np.ndarray` (N×3) | `[[0, 0, 2.2], [0, 0, -2.2]]` |
| `magnetizations` | Computed | `np.ndarray` (N,) | `[2.2, -2.2]` |
| `kind_names` | Computed | `list[str]` | `['Cu1', 'Cu1', 'O1']` |
| `weights` | Computed | `list[tuple]` | `[(0.7, 0.3), (1.0,)]` |

### Global Properties

| Property | Type | Format | Example |
|----------|------|--------|---------|
| `pbc` | Global | `list[bool]` | `[True, True, False]` |
| `cell` | Global | `np.ndarray` (3×3) | `[[3.0, 0, 0], [0, 3.0, 0], [0, 0, 5.0]]` |
| `tot_charge` | Global | `float` | `2.0` |
| `tot_magnetization` | Global | `float` | `4.4` |
| `hubbard` | Global | `Hubbard` class | Contains U and V parameters with site indices |

:::{note}
The `hubbard` property is global because it references site indices. For example:
- On-site U: `{'atom_index': 0, 'manifold': '3d', 'U': 4.0}`
- Inter-site V: `{'atom_index': 0, 'neighbour_index': 1, 'manifold': '3d', 'V': 1.0}`

Since these parameters involve references to specific sites (by index), they cannot be stored as individual site properties.
:::

### Accessing Properties

```python
# Access individual site property (singular)
structure.properties.sites[0].charge  # Single float value

# Access computed array property (plural)
structure.properties.charges  # np.ndarray with all charges

# Both return the same values:
structure.properties.charges[0] == structure.properties.sites[0].charge  # True
```
