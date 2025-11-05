# Querying Structures

Learn how to query and search for `StructureData` nodes in your AiiDA database using the QueryBuilder.

:::{note}
This page only concerns the `StructureData` object, as the `StructureBuilder` is just a python class with no utility in the AiiDA provenance database.
:::

## How Properties are Stored

In the AiiDA database, only properties that differ from their default values are stored. For example, if all charges are zero, the `charges` property won't be stored. This means structures in the database with a `charges` entry have at least one non-zero charge (though the total can still be neutral).
Moreover, `computed_fields` (i.e. derived properties from the user-defined ones) are also stored.

For any `StructureData` object, you can see which properties are stored using:

```python
structure.get_defined_properties()
```

:::{important}
The `sites` and `kinds`properties are **not** stored in the database—they are computed on-the-fly when we reload the node from the database, as they don't contain any additional information.

To see the raw database representation:
```python
print(structure.base.attributes.all.keys())
# Returns: dict_keys(['pbc', 'cell', 'cell_volume', 'dimensionality', 'formula', 'is_alloy', 'has_vacancies', 'positions', 'kind_names', 'symbols', 'masses', 'magmoms', 'site_indices'])
```
:::

## Queryable Properties

Get the full list of properties that is possible to query:

```python
StructureData.get_queryable_properties()
```

These include: `formula`, `symbols`, `kinds`, `masses`, `charges`, `magmoms`, `positions`, `cell_volume`, `dimensionality`, and more.

## Simple Queries

### All Structures

Query all `StructureData` in your database:

```python
from aiida.orm import QueryBuilder
from aiida_atomistic.data.structure import StructureData

qb = QueryBuilder()
qb.append(StructureData)
print(f"Total structures: {len(qb.all())}")
```

### Structures with Specific Properties

Find structures that have certain properties defined:

```python
# Structures with charges defined
prop = 'charges'
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'has_key': prop}}
)
print(f"Structures with {prop}: {len(qb.all())}")

# Structures with both charges AND magmoms
props = ['charges', 'magmoms']
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'and': [{'has_key': prop} for prop in props]}}
)
print(f"Structures with both properties: {len(qb.all())}")

# Structures with charges but NOT magmoms
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'and': [
        {'has_key': 'charges'},
        {'!has_key': 'magmoms'}
    ]}}
)
print(f"Structures with charges only: {len(qb.all())}")
```

### Structures without Specific Properties

Use the `!` negation:

```python
prop = 'magmoms'
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'!has_key': prop}}
)
print(f"Structures without {prop}: {len(qb.all())}")
```

### Projecting Specific Attributes

Retrieve only selected properties instead of full nodes:

```python
prop = 'charges'
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes': {'has_key': prop}},
    project=['attributes.formula', 'attributes.' + prop, 'id']
)

result = qb.all()[-1]  # Get last result
print(f"Formula: {result[0]}")
print(f"Charges: {result[1]}")
print(f"PK: {result[2]}")
```

### Structures by Number of Atoms

```python
# Less than 6 atoms
nr_atoms = 6
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.symbols': {'shorter': nr_atoms}}
)
print(f"Structures with < {nr_atoms} atoms: {len(qb.all())}")

# More than 5 atoms
nr_atoms = 5
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.symbols': {'longer': nr_atoms}}
)
print(f"Structures with > {nr_atoms} atoms: {len(qb.all())}")

# Exactly 2 atoms
nr_atoms = 2
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.symbols': {'and': [
        {'shorter': nr_atoms + 1},
        {'longer': nr_atoms - 1}
    ]}}
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
```

## Advanced Queries

### Specific Chemical Formula

```python
formula = 'HO'
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.formula': formula}  # or {'==': formula}
)
print(f"Structures with formula {formula}: {len(qb.all())}")
```

### Specific Number of Atoms of an Element

For multiple atoms of the same element:

```python
element = 'H'
nr_atoms = 2
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={
        'attributes.formula': {'like': f'%{element}{nr_atoms}%'}
    },
    project=['attributes.formula', 'id']
)
print(f"Structures with {nr_atoms} {element} atoms: {len(qb.all())}")
```

:::{warning}
This approach may match unintended formulas (e.g., searching for `Mn2` might also match `Mn20`). Use regex post-processing for precise matches.
:::

### Exactly One Atom of an Element

For a single atom, use regex to ensure no digits follow:

```python
import re

element = 'H'
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.formula': {'like': f'%{element}%'}},
    project=['attributes.formula', 'id']
)

res = []
for struct in qb.iterall():
    formula = struct[0]
    # Match H not followed by any digit
    if formula and re.search(f'{element}(?![0-9])', formula):
        res.append(struct)

print(f"Structures with exactly one {element}: {len(res)}")
```

**Regex explanation:**
- `H` - matches the element symbol
- `(?![0-9])` - negative lookahead: ensures H is NOT followed by a digit
- This matches formulas where H appears alone (exactly 1 atom)

### Exactly N Atoms of an Element

For precise matching of specific atom counts:

```python
element = 'Mn'
nr_atoms = 2
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.formula': {'like': f'%{element}{nr_atoms}%'}},
    project=['attributes.formula', 'id']
)

res = []
for struct in qb.iterall():
    formula = struct[0]
    # Match element followed by the number, but not by another digit
    if formula and re.search(f'{element}{nr_atoms}(?![0-9])', formula):
        res.append(struct)

print(f"Structures with exactly {nr_atoms} {element}: {len(res)}")
print(f"Formulas: {[s[0] for s in res]}")
```

### Binaries and Ternaries

Find structures with specific numbers of elements using regex:

```python
import re

# Binary compounds (2 elements)
number_of_elements = 2
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.symbols': {'longer': number_of_elements - 1}},
    project=['attributes.formula', 'id']
)

res = []
for struct in qb.iterall():
    formula = struct[0]
    # Pattern: exactly 2 occurrences of [Capital][lowercase]*[digits]*
    pattern = '^' + '[A-Z][a-z]*[0-9]*' * number_of_elements + '$'
    if formula and re.search(pattern, formula):
        res.append(struct)

print(f"Binary compounds: {len(res)}")
print(f"Examples: {[s[0] for s in res[:5]]}")

# Ternary compounds (3 elements)
number_of_elements = 3
qb = QueryBuilder()
qb.append(
    StructureData,
    filters={'attributes.symbols': {'longer': number_of_elements - 1}},
    project=['attributes.formula', 'id']
)

res = []
for struct in qb.iterall():
    formula = struct[0]
    pattern = '^' + '[A-Z][a-z]*[0-9]*' * number_of_elements + '$'
    if formula and re.search(pattern, formula):
        res.append(struct)

print(f"Ternary compounds: {len(res)}")
```

**Regex pattern explanation:**
- `^` - start of string
- `[A-Z]` - capital letter (element symbol start)
- `[a-z]*` - zero or more lowercase letters (element symbol continuation)
- `[0-9]*` - zero or more digits (stoichiometry)
- Repeated `number_of_elements` times
- `$` - end of string

This ensures the formula has exactly the specified number of element symbols.

## Best Practices

1. **Filter early**: Use QueryBuilder filters to reduce the result set before post-processing
2. **Project efficiently**: Only retrieve the attributes you need
3. **Use regex carefully**: Regex post-processing is powerful but slower than database filters
4. **Check for None**: Always validate that projected values exist before using them in regex
5. **Combine filters**: Use `and`, `or`, and negation (`!`) to build complex queries

## Performance Tips

- Use `qb.iterall()` instead of `qb.all()` for large result sets to avoid loading everything into memory
- Apply as many filters as possible at the database level before regex post-processing
- Use `project` to retrieve only needed attributes
- For very large databases, consider adding pagination with `limit` and `offset`

## See Also

- [AiiDA QueryBuilder Documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/howto/query.html)
- [QueryBuilder Filters Reference](https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/database.html#reference-tables)
- [Working with Kinds](kinds.md)
- [Magnetic Structures](magnetic_structures.md)
- [Property Types](../in_depth/properties.md)
