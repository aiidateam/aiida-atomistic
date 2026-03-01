# Querying Structures

Learn how to query and search for `StructureData` nodes in your AiiDA database using the QueryBuilder. For more details on the query of data from AiiDA databases, we refer to the [official documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/howto/query.html).

!!! note
    This page only concerns the `StructureData` object, as the `StructureBuilder` is just a python class with no utility in the AiiDA provenance database.

!!! note "Storage Locations"

    **Database (queryable via QueryBuilder):**

    - Global properties: `pbc`, `cell`, `periodicity`, `tot_magnetization`, `tot_charge`, `hubbard`, `custom` and so on. You can see the whole set accessing `StructureData.get_supported_properties()['global']`
    - Computed properties: `composition`, `cell_volume`, `dimensionality`, `is_alloy`, `has_vacancies`, `symbols`, `kind_names`, `n_sites` and so on. You can see the whole set accessing `StructureData.get_computed_properties()['global']`

    **Not stored (computed on-the-fly only):**

    - `formula` — use `structure.properties.formula` to access it, but it **cannot** be queried. Use `composition` for database queries instead.

    **Repository (not queryable, loaded on access):**

    - Per-site arrays: `positions`, `masses`, `charges`, `magmoms`, `magnetizations`, `weights`

    The `sites` and `kinds` properties are **never stored**—they are reconstructed on-the-fly from the stored data.


For any `StructureData` object, you can see which properties are stored using:

```python
structure.get_defined_properties()
```

## Queryable Properties

Get the full list of properties stored in the database that can be queried:

```python
StructureData.get_queryable_properties()
```

**Queryable properties include:**
- **Global**: `pbc`, `cell`, `periodicity`, `tot_magnetization`, `tot_charge`, `hubbard`, `custom`
- **Computed**: `composition`, `cell_volume`, `dimensionality`, `is_alloy`, `has_vacancies`, `symbols`, `kind_names`, `n_sites`
- **Statistics**: `max_charge`, `min_charge`, `max_magmom`, `min_magmom`, `max_magnetization`, `min_magnetization`

!!! note
**`formula` is no longer stored in the database** and therefore cannot be queried. Use `composition` instead — it is a `dict` mapping element symbols to their count, e.g. `{"Fe": 2, "O": 3}`, and is fully queryable.

## Examples of simple queries

Query all `StructureData` in your database:

```python
from aiida.orm import QueryBuilder
from aiida_atomistic.data.structure import StructureData

qb = QueryBuilder()
qb.append(StructureData)
print(f"Total structures: {len(qb.all())}")
```

**Output**
```text
Total structures: 8011
```

### Structures with specific properties

Find structures that have certain properties defined. Note that per-site arrays are in the repository, so we query their statistical summaries:

```python
# Structures with charges defined (via max_charge statistic)
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'has_key': 'max_charge'}}
)
print(f"Structures with charges: {len(qb.all())}")

# Structures with magnetic moments defined
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'has_key': 'max_magmom'}}
)
print(f"Structures with magmoms: {len(qb.all())}")

# Structures with both charges AND magmoms
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'and': [
        {'has_key': 'max_charge'},
        {'has_key': 'max_magmom'}
    ]}}
)
print(f"Structures with both properties: {len(qb.all())}")

# Structures with charges but NOT magmoms
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'and': [
        {'has_key': 'max_charge'},
        {'!has_key': 'max_magmom'}
    ]}}
)
print(f"Structures with charges only: {len(qb.all())}")
```

### Structures without Specific Properties

Use the `!` negation to find structures without specific properties:

```python
# Structures without charges
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'!has_key': 'max_charge'}}
)
without_charges = len(qb.all())
print(f"Structures without charges: {len(qb.all())}")
```

### Projecting Specific Attributes

Retrieve only selected properties instead of full nodes:

```python
# Get formula and statistics for structures with charges
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'has_key': 'max_charge'}},
    project=['attributes.formula', 'attributes.max_charge', 'attributes.min_charge', 'id']
)

result = qb.all()[-1]  # Get last result
print(f"Formula: {result[0]}")
print(f"Max charge: {result[1]}")
print(f"Min charge: {result[2]}")
print(f"PK: {result[3]}")
```

### Structures by Number of Atoms

Use `attributes.n_sites` for total atom count:

```python
# Less than 6 atoms
nr_atoms = 6
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.n_sites': {'<': nr_atoms}}
)
print(f"Structures with < {nr_atoms} atoms: {len(qb.all())}")

# More than 5 atoms
nr_atoms = 5
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.n_sites': {'>': nr_atoms}}
)
print(f"Structures with > {nr_atoms} atoms: {len(qb.all())}")

# Exactly 2 atoms
nr_atoms = 2
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.n_sites': nr_atoms}
)
print(f"Structures with exactly {nr_atoms} atoms: {len(qb.all())}")
```

### Alloys and Vacancies

Find structures with alloys or vacancies:

```python
# Structures with alloys
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.is_alloy': True}
)

# Structures with vacancies
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.has_vacancies': True}
)
print(f"Structures with vacancies: {len(qb.all())}")
```

### Querying by Statistical Properties

Since per-site properties are stored in the repository, use statistical summaries to filter by value ranges:

```python
# Structures with charges above a threshold
charge_threshold = 1.0
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.max_charge': {'>': charge_threshold}}
)
print(f"Structures with max charge > {charge_threshold}: {len(qb.all())}")

# Structures with charge range between min and max
min_charge = -1.0
max_charge = 1.0
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'and': [
        {'attributes.min_charge': {'>': min_charge}},
        {'attributes.max_charge': {'<': max_charge}}
    ]}
)
print(f"Structures with charges in ({min_charge}, {max_charge}): {len(qb.all())}")
```

!!! tip
**Using Statistics for Efficient Queries**

    Statistical properties enable efficient filtering without loading large arrays:

    - Use `max_charge` and `min_charge` to find structures with specific charge distributions
    - Use `max_magmom` and `min_magmom` to filter by magnetic moment magnitudes
    - Combine with other filters like `formula` or `n_sites` for precise queries
    - Remember: `min_magmom` and `max_magmom` represent the **magnitude** of magnetic moment vectors


## Advanced Queries

### Specific Chemical Formula

`formula` is no longer stored in the database. Use `composition` to search by element
content instead. `composition` is a `dict` like `{"Fe": 2, "O": 3}`, stored as a
JSON attribute, so all standard QueryBuilder dict/key filters apply.

```python
# Structures containing iron
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.composition': {'has_key': 'Fe'}}
)
print(f"Structures containing Fe: {len(qb.all())}")

# Structures containing both Fe and O
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.composition': {'and': [
        {'has_key': 'Fe'},
        {'has_key': 'O'},
    ]}}
)
print(f"Fe-O structures: {len(qb.all())}")
```

### Specific Number of Atoms of an Element

Because `composition` is a queryable dict, you can filter on the **count** of an element
directly — no regex needed:

```python
# Exactly 2 Fe atoms
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.composition.Fe': 2},
    project=['attributes.composition', 'id']
)
print(f"Structures with exactly 2 Fe: {len(qb.all())}")

# At least 3 H atoms
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.composition.H': {'>': 2}},
    project=['attributes.composition', 'id']
)
print(f"Structures with ≥ 3 H: {len(qb.all())}")
```

### Binaries and Ternaries

`composition` stores one key per distinct element, so the number of keys equals the
number of distinct elements. Use `has_key` / `!has_key` to check for the presence of
elements, or load the node and check `len(structure.properties.composition)`:

```python
# Binary compounds (exactly 2 distinct elements) — database-side pre-filter
# then Python-side length check
qb = QueryBuilder()
qb.append(StructureData, project=['*'])

binaries = [
    s for (s,) in qb.iterall()
    if len(s.properties.composition) == 2
]
print(f"Binary compounds: {len(binaries)}")
print(f"Examples: {[s.properties.formula for s in binaries[:5]]}")

# If your database is large, pre-filter with a known element to reduce the scan:
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.composition': {'has_key': 'Fe'}},
    project=['*']
)
fe_binaries = [
    s for (s,) in qb.iterall()
    if len(s.properties.composition) == 2
]
print(f"Fe-containing binaries: {len(fe_binaries)}")
```
