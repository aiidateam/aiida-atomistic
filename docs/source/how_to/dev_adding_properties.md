# Adding a New Property: Step-by-Step

This guide explains how to add new properties to `StructureData` and `StructureBuilder`.

This guide covers two types of properties:
1. **Site properties** - Properties that vary per atom (e.g., `new_site_property`)
2. **Global properties** - Properties that apply to the entire structure (e.g., `new_global_property`)

## Before You Start: Contributing to aiida-atomistic

If you want to add a new property to the official `aiida-atomistic` package:

### 1. Fork the Repository

Go to the [aiida-atomistic GitHub repository](https://github.com/aiidateam/aiida-atomistic) and click the "Fork" button to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/aiida-atomistic.git
cd aiida-atomistic
```

### 3. Create a Feature Branch

```bash
git checkout -b add-new-property
```

### 4. Install in Development Mode

```bash
pip install -e .[dev]
```

Now you can make changes and they'll be immediately reflected in your Python environment.

### 5. After Making Changes

Once you've completed the steps below and added tests:

```bash
# Run tests
pytest tests/

# Commit your changes
git add .
git commit -m "Add new_site_property to Site model"

# Push to your fork
git push origin add-new-property
```

### 6. Create a Pull Request

Go to your fork on GitHub and click "New Pull Request". Provide a clear description of:
- What property you're adding
- Why it's useful
- Any relevant scientific context
- Link to related issues (if any)

:::{tip}
Before creating a PR, it's a good idea to open an issue on the main repository to discuss whether the property should be added. The maintainers can provide guidance on the best implementation approach.
:::

---

## Adding a Site Property

Let's add a hypothetical `new_site_property` (a scalar value per site, like an effective nuclear charge or local electric field strength).

### Step 1: Add Field to the Site Model

Edit `src/aiida_atomistic/data/structure/site.py`:

```python
class Site(BaseModel):
    # ... existing fields ...

    new_site_property: t.Optional[float] = Field(
        default=None,
        json_schema_extra={"tolerance": 1e-4},
        description="Description of the new site property"
    )
```

:::{tip}
Add `json_schema_extra={"tolerance": value}` to define the default tolerance for kind classification. This tolerance will be used when comparing sites to determine if they belong to the same kind.
:::

### Step 2: Add to Site Property Dictionary

Edit `src/aiida_atomistic/data/structure/__init__.py`:

```python
_SITE_PROPERTIES = [
    # ... existing properties ...
    'new_site_property',  # Add here
]

# Add default value if needed
_DEFAULT_VALUES = {
    # ... existing defaults ...
    'new_site_property': 0.0,
}
```

### Step 3: Add Computed Field (for array access)

If the property should be accessible as an array, add a computed field in `models.py`:

```python
@computed_field(json_schema_extra={"store_in": "repository", "property_type": "computed"})
@property
def new_site_properties(self) -> t.Optional[np.ndarray]:
    """
    Return the new_site_property values of all sites as a numpy array.

    Returns:
        np.ndarray: An array of values corresponding to each site, or None if not set.
    """
    if all(site.new_site_property is None for site in self.sites):
        return None
    return np.array([
        site.new_site_property if site.new_site_property is not None
        else _DEFAULT_VALUES['new_site_property']
        for site in self.sites
    ])
```

:::{note}
The computed field name is typically the plural form of the site property name (e.g., `new_site_property` → `new_site_properties`). This allows accessing all values at once as an array.
:::

#### Storage Metadata

The `json_schema_extra` parameter controls how the property is stored:

**For repository-based storage (`StructureDataRepository`):**

| Metadata Key | Values | Purpose |
|--------------|--------|---------|
| `store_in` | `"npz"`, `"repo"`, `"repository"` | Store in repository `.npz` file |
|  | `"db"`, `"attribute"`, `"attributes"` | Store in database attributes (queryable) |
| `property_type` | `"global"`, `"computed"`, `"internal"` | Classification |

**Examples:**

```python
# Store array in repository (efficient for large arrays)
@computed_field(json_schema_extra={"store_in": "repository", "property_type": "computed"})
@property
def positions(self) -> np.ndarray:
    return np.array([site.position for site in self.sites])

# Store metadata in database (queryable)
@computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
@property
def formula(self) -> str:
    return self._compute_formula()

# Not stored, computed on-the-fly
@computed_field(json_schema_extra={"property_type": "computed"})
@property
def kinds(self) -> list[Kind]:
    return self._compute_kinds()
```

**Decision Guide:**

- **Use `store_in="npz"`** for:
  - Large numeric arrays (positions, charges, magmoms)
  - Site-level properties with many atoms
  - Properties not needed for queries

- **Use `store_in="db"`** for:
  - Queryable metadata (formula, volume, statistics)
  - Small properties used in searches
  - Properties needed for filtering

- **Omit `store_in`** for:
  - Properties reconstructed from other data (kinds)
  - Internal representations
  - Expensive computations done on-demand

See [Storage Backends](../in_depth/storage_backends.md) for more details.

#### Singular Form Metadata (Required for Site-Array Properties)

:::{important}
**For all computed fields that represent site-level properties (plural arrays), you MUST include `singular_form` in the metadata.**
:::

The `singular_form` metadata tells the loading mechanism how to map the plural array property back to individual site properties:

```python
@computed_field(
    json_schema_extra={
        "store_in": "repository",
        "property_type": "computed",
        "singular_form": "new_site_property"  # ← REQUIRED for site arrays
    }
)
@property
def new_site_properties(self) -> t.Optional[np.ndarray]:
    """Array of new_site_property values from all sites."""
    return np.array([site.new_site_property for site in self.sites])
```

**Why is this needed?**

When a structure is loaded from the database, the system reconstructs the sites from stored arrays:
1. Loads `new_site_properties` array: `[1.5, 2.3, 4.1]`
2. Checks metadata for `singular_form`: `"new_site_property"`
3. Creates sites with: `{"position": [...], "new_site_property": 1.5}`, etc.

**Without `singular_form`:**
- ❌ Loading fails with `KeyError`
- ❌ Sites are not properly reconstructed
- ❌ Properties are lost after storing/loading

**Common Examples:**

| Plural Property | `singular_form` Value |
|----------------|----------------------|
| `positions` | `"position"` |
| `symbols` | `"symbol"` |
| `masses` | `"mass"` |
| `charges` | `"charge"` |
| `magmoms` | `"magmom"` |
| `magnetizations` | `"magnetization"` |
| `weights` | `"weight"` |
| `kind_names` | `"kind_name"` |
| `new_site_properties` | `"new_site_property"` |

**When NOT to include `singular_form`:**

Properties that don't map to site-level fields:
- `formula` (global string)
- `n_sites` (count)
- `max_charge`, `min_charge` (statistics)
- `kinds` (computed from sites)

### Step 4: Add Setter Method

Add a setter method in `src/aiida_atomistic/data/structure/setter_mixin.py`:

```python
def set_new_site_property(self, values: t.Union[list, np.ndarray]):
    """
    Set the new_site_property values for all sites.

    Args:
        values: Array of values, one per site.

    Raises:
        ValueError: If length doesn't match number of sites.
        TypeError: If called on an immutable structure.
    """
    if not isinstance(self, StructureBuilder):
        raise TypeError("Can only set properties on StructureBuilder")

    values = np.asarray(values)

    if len(values) != len(self.properties.sites):
        raise ValueError(
            f"Length of values ({len(values)}) must match "
            f"number of sites ({len(self.properties.sites)})"
        )

    for i, value in enumerate(values):
        self.properties.sites[i].new_site_property = float(value)
```

### Step 5: Add Getter Method

Add a getter method in `src/aiida_atomistic/data/structure/getter_mixin.py`:

```python
def get_new_site_property(self) -> t.Optional[np.ndarray]:
    """
    Get the new_site_property values for all sites.

    Returns:
        np.ndarray: Array of values, or None if not set.
    """
    return self.properties.new_site_property
```

### Step 6: Add Remove Method

Add a remove method in `src/aiida_atomistic/data/structure/setter_mixin.py`:

```python
def remove_new_site_property(self):
    """
    Remove new_site_property from all sites.
    """

    self.remove_property('new_site_property')
        return
```

:::{important}
**Why Remove Methods Are Important:**
- Allow users to clean up properties they no longer need
- Help create different variations of structures for testing
- Essential for structure manipulation workflows
- Should be documented alongside setters in guides
:::

### Step 7: Add Validation (optional)

Add validation in the `Site` model if needed:

```python
@field_validator('new_site_property')
@classmethod
def validate_new_site_property(cls, v):
    """Validate new_site_property value."""
    if v is not None and (v < -10.0 or v > 10.0):
        raise ValueError(f"new_site_property must be between -10 and 10, got {v}")
    return v
```

### Step 7: Add Tests

Create tests in `tests/data/test_models.py` or appropriate test file:

```python
def test_new_site_property():
    """Test new_site_property."""
    structure_dict = {
        "pbc": [True, True, True],
        "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        "sites": [
            {"symbol": "Fe", "position": [0, 0, 0], "new_site_property": 1.5},
            {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "new_site_property": 2.3},
        ],
    }

    structure = StructureData(**structure_dict)
    assert np.allclose(structure.properties.new_site_property, [1.5, 2.3])

    # Test setter for mutable
    mutable = StructureBuilder(**structure_dict)
    mutable.set_new_site_property([3.1, 4.2])
    assert np.allclose(mutable.get_new_site_property(), [3.1, 4.2])
```

### Step 8: Update Documentation

Add the property to the documentation:

1. Add to property tables in guides
2. Add usage examples
3. Document any special behavior or constraints

---

## Adding a Global Property

Let's add a hypothetical `new_global_property` (a property that applies to the entire structure, like temperature or pressure).

### Step 1: Add Field to the Structure Model

Edit `src/aiida_atomistic/data/structure/models.py`:

```python
class StructureBaseModel(BaseModel):
    # ... existing fields ...

    new_global_property: t.Optional[float] = Field(
        default=None,
        description="Description of the new global property (e.g., temperature in K)"
    )
```

### Step 2: Add to Global Property Dictionary

Edit `src/aiida_atomistic/data/structure/__init__.py`:

```python
_GLOBAL_PROPERTIES = [
    # ... existing properties ...
    'new_global_property',  # Add here
]

# Add default value if needed
_DEFAULT_VALUES = {
    # ... existing defaults ...
    'new_global_property': 300.0,  # e.g., room temperature
}
```

### Step 3: Add Setter Method (if needed)

For mutable structures, add a setter method in `setter_mixin.py`:

```python
def set_new_global_property(self, value: float):
    """
    Set the new_global_property.

    Args:
        value: The new value for the global property.

    Raises:
        TypeError: If called on an immutable structure.
    """
    if not isinstance(self, StructureBuilder):
        raise TypeError("Can only set properties on StructureBuilder")

    self.properties.new_global_property = float(value)
```

### Step 4: Add Getter Method (if needed)

Add a getter method in `getter_mixin.py`:

```python
def get_new_global_property(self) -> t.Optional[float]:
    """
    Get the new_global_property value.

    Returns:
        float: The global property value, or None if not set.
    """
    return self.properties.new_global_property
```

### Step 5: Add Remove Method (if needed)

Add a remove method in `setter_mixin.py`:

```python
def remove_new_global_property(self):
    """
    Remove the new_global_property.
    """

    self.remove_property('new_global_property')
        return
```

### Step 6: Add Validation (optional)

Add validation in `StructureBaseModel` if needed:

```python
@field_validator('new_global_property')
@classmethod
def validate_new_global_property(cls, v):
    """Validate new_global_property value."""
    if v is not None and v < 0:
        raise ValueError(f"new_global_property must be non-negative, got {v}")
    return v
```

### Step 7: Add Tests

Create tests in `tests/data/test_models.py`:

```python
def test_new_global_property():
    """Test new_global_property."""
    structure_dict = {
        "pbc": [True, True, True],
        "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        "sites": [{"symbol": "Fe", "position": [0, 0, 0]}],
        "new_global_property": 500.0,
    }

    structure = StructureData(**structure_dict)
    assert structure.properties.new_global_property == 500.0

    # Test setter for mutable
    mutable = StructureBuilder(**structure_dict)
    mutable.set_new_global_property(600.0)
    assert mutable.get_new_global_property() == 600.0

    # Test remove method
    mutable.remove_new_global_property()
    assert mutable.get_new_global_property() is None
```

### Step 8: Update Documentation

Document the new global property with usage examples.

---

## Complete Checklist

When adding a new **site property**, ensure you:

- [ ] Add field to `Site` model in `site.py`
- [ ] Add `json_schema_extra={"tolerance": value}` for kind classification
- [ ] Add to `_SITE_PROPERTIES` list in `__init__.py`
- [ ] Add default value (if applicable) in `_DEFAULT_VALUES`
- [ ] Add computed field (for array access) in `models.py`
- [ ] **Add `singular_form` metadata to computed field** (maps plural → singular)
- [ ] Add `store_in` metadata (`"npz"` or `"db"`) to computed field
- [ ] Add setter method in `setter_mixin.py`
- [ ] Add getter method in `getter_mixin.py`
- [ ] Add remove method in `setter_mixin.py`
- [ ] Add validation (if needed) in model validators
- [ ] Add comprehensive tests (including remove functionality)
- [ ] Update documentation with examples
- [ ] Add to property reference tables

When adding a new **global property**, ensure you:

- [ ] Add field to `StructureBaseModel` in `models.py`
- [ ] Add to `_GLOBAL_PROPERTIES` list in `__init__.py`
- [ ] Add default value (if applicable) in `_DEFAULT_VALUES`
- [ ] Add setter method (if needed) in `setter_mixin.py`
- [ ] Add getter method (if needed) in `getter_mixin.py`
- [ ] Add remove method (if needed) in `setter_mixin.py`
- [ ] Add validation (if needed) in model validators
- [ ] Add comprehensive tests (including remove functionality)
- [ ] Update documentation with examples

## Common Pitfalls

### ❌ Direct Modification in Mutable Structures

```python
# ❌ BAD: Bypasses validation and can cause inconsistencies
mutable_structure.properties.sites[0].new_site_property = 1.5

# ✅ GOOD: Uses setter method with validation
mutable_structure.set_new_site_property([1.5, 2.3])
```

### ❌ Forgetting to Update Property Dictionaries

```python
# If you add a field but forget to add it to _SITE_PROPERTIES or _GLOBAL_PROPERTIES:
# - It won't be included in to_dict()
# - It won't be stored properly
# - Kind-based compression will ignore it (for site properties)
```

### ❌ Missing Computed Field for Site Properties

```python
# Without computed field:
structure.properties.sites[0].new_site_property  # ✅ Works
structure.properties.new_site_property  # ❌ AttributeError

# With computed field:
structure.properties.new_site_property  # ✅ Returns np.array([...])
```

### ❌ Forgetting Tolerance for Site Properties

```python
# Without tolerance in json_schema_extra:
# - Default tolerance (1e-3) will be used for kind classification
# - May not be appropriate for your property's precision

# With tolerance:
new_site_property: t.Optional[float] = Field(
    default=None,
    json_schema_extra={"tolerance": 1e-4}  # ✅ Appropriate for this property
)
```

### ❌ Missing `singular_form` in Computed Field Metadata

```python
# ❌ BAD: Missing singular_form - loading from database will FAIL
@computed_field(json_schema_extra={"store_in": "repository", "property_type": "computed"})
@property
def new_site_properties(self) -> np.ndarray:
    return np.array([site.new_site_property for site in self.sites])

# Result: KeyError when loading stored structures

# ✅ GOOD: Includes singular_form mapping
@computed_field(
    json_schema_extra={
        "store_in": "repository",
        "property_type": "computed",
        "singular_form": "new_site_property"  # Maps plural → singular
    }
)
@property
def new_site_properties(self) -> np.ndarray:
    return np.array([site.new_site_property for site in self.sites])

# Result: Structure loads correctly from database
```

:::{danger}
**Critical**: Always add `singular_form` to computed fields that represent site-level arrays. Without it:
- Structures cannot be loaded from the database
- Site reconstruction fails with `KeyError`
- All stored data becomes inaccessible
:::

## Examples

### Example 1: Adding Occupation Numbers (Site Property)

```python
# 1. Add to Site model in site.py
class Site(BaseModel):
    occupation: t.Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        json_schema_extra={"tolerance": 1e-3},
        description="Site occupation number (0-1)"
    )

# 2. Add to __init__.py
_SITE_PROPERTIES = [..., 'occupation']
_DEFAULT_VALUES = {..., 'occupation': 1.0}

# 3. Add computed field in models.py
@computed_field(
    json_schema_extra={
        "store_in": "repository",
        "property_type": "computed",
        "singular_form": "occupation"  # Required for loading
    }
)
@property
def occupations(self) -> t.Optional[np.ndarray]:
    if all(site.occupation is None for site in self.sites):
        return None
    return np.array([
        site.occupation if site.occupation is not None else 1.0
        for site in self.sites
    ])

# 4. Add setter in setter_mixin.py
def set_occupations(self, occupations: t.Union[list, np.ndarray]):
    if not isinstance(self, StructureBuilder):
        raise TypeError("Can only set properties on StructureBuilder")
    occupations = np.asarray(occupations)
    if len(occupations) != len(self.properties.sites):
        raise ValueError(f"Length mismatch: {len(occupations)} vs {len(self.properties.sites)}")
    for i, occ in enumerate(occupations):
        self.properties.sites[i].occupation = float(occ)

# 5. Add getter in getter_mixin.py
def get_occupations(self) -> t.Optional[np.ndarray]:
    return self.properties.occupations

# 6. Use it
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "sites": [
        {"symbol": "Fe", "position": [0, 0, 0], "occupation": 0.95},
        {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "occupation": 0.90},
    ]
}
structure = StructureData(**structure_dict)
print(structure.properties.occupations)  # [0.95, 0.9]
```

### Example 2: Adding Temperature (Global Property)

```python
# 1. Add to StructureBaseModel in models.py
class StructureBaseModel(BaseModel):
    temperature: t.Optional[float] = Field(
        default=None,
        ge=0,
        description="Temperature in Kelvin"
    )

# 2. Add to __init__.py
_GLOBAL_PROPERTIES = [..., 'temperature']
_DEFAULT_VALUES = {..., 'temperature': 300.0}

# 3. Add setter in setter_mixin.py
def set_temperature(self, temperature: float):
    if not isinstance(self, StructureBuilder):
        raise TypeError("Can only set properties on StructureBuilder")
    if temperature < 0:
        raise ValueError("Temperature must be non-negative")
    self.properties.temperature = float(temperature)

# 4. Add getter in getter_mixin.py
def get_temperature(self) -> t.Optional[float]:
    return self.properties.temperature

# 5. Use it
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
    "sites": [{"symbol": "Fe", "position": [0, 0, 0]}],
    "temperature": 500.0,
}
structure = StructureData(**structure_dict)
print(structure.properties.temperature)  # 500.0

# For mutable structures
mutable = StructureBuilder(**structure_dict)
mutable.set_temperature(600.0)
print(mutable.get_temperature())  # 600.0
```

### Example 3: Adding Temperature Factor / B-factor (Site Property with Validation)

```python
# Add as site property with validation
class Site(BaseModel):
    b_factor: t.Optional[float] = Field(
        default=None,
        ge=0,
        json_schema_extra={"tolerance": 1e-2},
        description="Temperature factor (B-factor) in Ų"
    )

    @field_validator('b_factor')
    @classmethod
    def validate_b_factor(cls, v):
        if v is not None and v > 100:
            warnings.warn(f"Unusually high B-factor: {v} Ų")
        return v

# Usage
structure_dict = {
    "pbc": [True, True, True],
    "cell": [[5.0, 0, 0], [0, 5.0, 0], [0, 0, 5.0]],
    "sites": [
        {"symbol": "C", "position": [0, 0, 0], "b_factor": 15.2},
        {"symbol": "C", "position": [2.5, 2.5, 2.5], "b_factor": 18.7},
    ]
}
```

### Example 4: Adding Statistical Computed Fields (Max/Min Values)

When you add a site property that stores per-atom values (like charges, magnetic moments, etc.), you should also add **statistical computed fields** for efficient querying. These fields store aggregated metadata (max, min, average) in the database so users can filter structures without loading the full arrays.

**Use Case:** You want to find all structures with high charges without loading every structure's full charge array.

#### Step-by-Step: Adding Statistics for a New Site Property

Let's add statistics for a hypothetical `spin_density` property:

```python
# 1. First, add the site property and its computed field (as shown in previous examples)
class Site(BaseModel):
    spin_density: t.Optional[float] = Field(
        default=None,
        json_schema_extra={"tolerance": 1e-3},
        description="Spin density at this site"
    )

# 2. Add computed field for array access in models.py
@computed_field(json_schema_extra={"store_in": "repository", "property_type": "computed"})
@property
def spin_densities(self) -> t.Optional[np.ndarray]:
    """Spin density values for all sites (stored in repository)."""
    if all(site.spin_density is None for site in self.sites):
        return None
    return np.array([
        site.spin_density if site.spin_density is not None else 0.0
        for site in self.sites
    ])

# 3. Add statistical computed fields (stored in database for querying)
@computed_field(json_schema_extra={"property_type": "computed", "store_in": "db", "statistic": "max"})
@property
def max_spin_density(self) -> t.Optional[float]:
    """Maximum spin density value across all sites (queryable)."""
    if self.spin_densities is None:
        return None
    return float(np.max(self.spin_densities))

@computed_field(json_schema_extra={"property_type": "computed", "store_in": "db", "statistic": "min"})
@property
def min_spin_density(self) -> t.Optional[float]:
    """Minimum spin density value across all sites (queryable)."""
    if self.spin_densities is None:
        return None
    return float(np.min(self.spin_densities))

@computed_field(json_schema_extra={"property_type": "computed", "store_in": "db", "statistic": "has"})
@property
def has_spin_density(self) -> bool:
    """Whether any site has spin density defined (queryable)."""
    return self.spin_densities is not None
```

#### Real Example: Charges with Statistics

This is how charges are implemented in `aiida-atomistic`:

```python
# In models.py

# Array computed field (stored in .npz repository)
@computed_field(json_schema_extra={"store_in": "repository", "property_type": "computed"})
@property
def charges(self) -> t.Optional[np.ndarray]:
    """Charge values for all sites."""
    if all(site.charge is None for site in self.sites):
        return None
    return np.array([
        site.charge if site.charge is not None else 0.0
        for site in self.sites
    ])

# Statistical fields (stored in database attributes - queryable!)
@computed_field(json_schema_extra={"property_type": "computed", "store_in": "db", "statistic": "max"})
@property
def max_charge(self) -> t.Optional[float]:
    """Maximum charge value across all sites."""
    if self.charges is None:
        return None
    return float(np.max(self.charges))

@computed_field(json_schema_extra={"property_type": "computed", "store_in": "db", "statistic": "min"})
@property
def min_charge(self) -> t.Optional[float]:
    """Minimum charge value across all sites."""
    if self.charges is None:
        return None
    return float(np.min(self.charges))
```

#### Metadata Keys Explained

| Metadata Key | Value | Purpose |
|--------------|-------|---------|
| `store_in` | `"db"` | Store in database attributes (makes it queryable) |
| `property_type` | `"computed"` | Indicates this is a computed field |
| `statistic` | `"max"`, `"min"`, `"avg"`, `"has"` | Classification (optional, for documentation) |

#### Special Cases

**For Vector Properties (like magmoms):**

When the property is a 3D vector, use the **magnitude** for max/min:

```python
# magmoms is N×3 array
@computed_field(json_schema_extra={"property_type": "computed", "store_in": "db", "statistic": "max"})
@property
def max_magmom(self) -> t.Optional[float]:
    """Maximum magnetic moment magnitude across all sites."""
    if self.magmoms is None:
        return None
    # Use np.linalg.norm to get magnitude of 3D vectors
    return float(np.max(np.linalg.norm(self.magmoms, axis=1)))

@computed_field(json_schema_extra={"property_type": "computed", "store_in": "db", "statistic": "min"})
@property
def min_magmom(self) -> t.Optional[float]:
    """Minimum magnetic moment magnitude across all sites."""
    if self.magmoms is None:
        return None
    return float(np.min(np.linalg.norm(self.magmoms, axis=1)))
```

#### Why Add Statistics?

**Without statistics:**
```python
# ❌ Cannot query - charge array is in .npz file
qb = QueryBuilder()
qb.append(StructureDataRepository, filters={'attributes.charges': ...})  # ERROR!
```

**With statistics:**
```python
# ✅ Can query efficiently using statistics
qb = QueryBuilder()
qb.append(
    StructureDataRepository,
    filters={
        'attributes.max_charge': {'>': 0.5},  # Find high charges
        'attributes.min_charge': {'<': -0.5}, # Find negative charges
    }
)

# Then load only matching structures
for structure in qb.all():
    charges = structure.charges  # Load full array only when needed
```

#### Checklist for Adding Statistics

When adding a new site property with statistics:

- [ ] Add site property field to `Site` model
- [ ] Add array computed field with `store_in="npz"`
- [ ] Add `max_<property>` with `store_in="db"` and `statistic="max"`
- [ ] Add `min_<property>` with `store_in="db"` and `statistic="min"`
- [ ] For vector properties, use `np.linalg.norm()` to get magnitude
- [ ] Add `has_<property>` boolean flag if useful for queries
- [ ] Include conditional checks (`if self.<property> is None: return None`)
- [ ] Convert to Python types with `float()`, `int()`, or `bool()`
- [ ] Add tests for statistics calculation
- [ ] Document in query examples

#### Common Statistical Fields

Here are common patterns for different property types:

```python
# Scalar property (charge, occupation, etc.)
@computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
@property
def max_<property>(self) -> t.Optional[float]:
    if self.<properties> is None:
        return None
    return float(np.max(self.<properties>))

# Vector property (magmom, velocity, etc.)
@computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
@property
def max_<property>(self) -> t.Optional[float]:
    if self.<properties> is None:
        return None
    return float(np.max(np.linalg.norm(self.<properties>, axis=1)))

# Boolean presence indicator
@computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
@property
def has_<property>(self) -> bool:
    return self.<properties> is not None

# Count (e.g., number of sites with property)
@computed_field(json_schema_extra={"store_in": "db", "property_type": "computed"})
@property
def n_sites_with_<property>(self) -> int:
    if self.<properties> is None:
        return 0
    return int(np.sum(self.<properties> != 0))  # or other condition
```

#### Testing Statistics

Add tests to verify statistics are calculated correctly:

```python
def test_spin_density_statistics():
    """Test statistical fields for spin_density."""
    structure_dict = {
        "pbc": [True, True, True],
        "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        "sites": [
            {"symbol": "Fe", "position": [0, 0, 0], "spin_density": 2.5},
            {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "spin_density": -1.8},
            {"symbol": "O", "position": [0.5, 0.5, 0.5], "spin_density": 0.3},
        ],
    }

    structure = StructureData(**structure_dict)

    # Test statistics
    assert structure.properties.max_spin_density == 2.5
    assert structure.properties.min_spin_density == -1.8
    assert structure.properties.has_spin_density is True

    # Test queryability (for repository-based storage)
    structure_repo = StructureDataRepository(**structure_dict)
    structure_repo.store()

    qb = QueryBuilder()
    qb.append(
        StructureDataRepository,
        filters={'attributes.max_spin_density': {'>': 2.0}}
    )
    assert qb.count() == 1
```

## Submitting Your Contribution

After implementing your new property following all the steps above:

### 1. Make Sure Everything Works

```bash
# Run the full test suite
pytest tests/

# Run tests for your specific property
pytest tests/data/test_models.py::test_new_site_property -v

# Check code style (if using pre-commit hooks)
pre-commit run --all-files
```

### 2. Update Documentation

Make sure you've updated:
- [ ] Property tables in `docs/source/in_depth/properties.md`
- [ ] Usage examples in relevant tutorials
- [ ] API reference documentation (docstrings)
- [ ] Changelog with a brief note about the new property

### 3. Create a Pull Request

Your PR description should include:

```markdown
## Description
Brief description of what property you're adding and why.

## Changes
- Added `new_site_property` to Site model
- Added setter/getter methods
- Added computed field for array access
- Added validation
- Added comprehensive tests
- Updated documentation

## Scientific Context
Explain the scientific use case for this property (e.g., "Used in MD for...").

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Follows existing code style
- [ ] Added to CHANGELOG.md

## Related Issues
Closes #XXX (if applicable)
```

:::{tip}
**For Personal/Plugin-Specific Properties**

If your property is very specific to your use case and not generally applicable, consider:
- Using the `custom` dictionary in structures instead
- Creating a plugin that extends `aiida-atomistic`
- Keeping it in your own fork for personal use

Only submit properties to the main repository that have broad applicability to the community.
:::

## Further Reading

- [Immutability Guide](../in_depth/immutability.md)
- [Kinds Documentation](../in_depth/kinds.md)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Contributing Guidelines](https://github.com/aiidateam/aiida-atomistic/blob/main/CONTRIBUTING.md)
