# Adding new properties in the `StructureData`: Step-by-Step

This guide explains how to add new properties to `StructureData` and `StructureBuilder`.

:::{note}
If you want to add a temporary/experimental property, you can add it as [custom property](../how_to/define_custom.md).
If instead you want to contribute to this package, this is the right page!
:::

This guide covers two types of properties:
1. **Site properties** - Properties that vary per atom (e.g., `charge`)
2. **Global properties** - Properties that apply to the entire structure (e.g., `tot_charge`)

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

### 4. Install in Editable Mode

```bash
pip install -e .
```

Now you can make changes and they'll be immediately reflected in your Python environment.

### 5. Create a Pull Request

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

Suppose you want to add a new `property_A` (a scalar value per site, like an effective nuclear charge or local electric field strength). The following steps are required in order to be coehrent with the current implementation of the `StructureData` node class.

### Step 1: Add Field to the Site Model

Edit `src/aiida_atomistic/data/structure/site.py`:

```python
class Site(BaseModel):
    # ... existing fields ...

    property_A: t.Optional[float] = Field(
        default=None,  # Always None - see explanation below
        json_schema_extra={
            "threshold": 1e-4, # Default tolerance for kind classification
            "default": 1.0  # Default value for array expansion - see explanation below
        },
        description="Description of the property_A"
    )
```

:::{important}
**Why `default=None` in Field and `"default"` in `json_schema_extra`?**

We use a two-level default system:

1. **Field `default=None`**: This is the Pydantic field default. Setting it to `None` means:
   - When you create a site without specifying `property_A`, the field is truly undefined (`None`)
   - This lets us distinguish between "property not set" vs "property set to zero"
   - Without this, if we used `default=0.0`, every site would appear to have `property_A` defined, even when unset

2. **`json_schema_extra["default"]`**: This is used when expanding arrays:
   - When one site has `property_A=2.5` but another has `property_A=None`
   - The array needs a concrete value for the undefined site, if the above condition is verified
   - We use `Site.get_default_values()['property_A']` to get `0.0` as the fill value
   - Result: `charges = [2.5, 0.0]` (not `[2.5, None]` which breaks numpy arrays)

**Example:**
```python
# Without property_A set
site1 = Site(symbol="Fe", position=[0, 0, 0])
site1.property_A  # None - we know it's undefined

# With property_A set to zero
site2 = Site(symbol="Fe", position=[0, 0, 0], property_A=0.0)
site2.property_A  # 0.0 - explicitly set

# Array expansion uses json_schema_extra["default"]
structure = StructureData(sites=[site1, site2])
structure.properties.property_A_array  # [1.0, 0.0] - we populated property_A_array[0] with the json_schema_extra["default"] = 1
```

This pattern allows:

- Detecting if a property is truly set or not
- Creating valid numpy arrays without `None` values
- Distinguishing "zero" from "undefined"
:::

You can also a validation, if needed:

```python
@field_validator('property_A')
@classmethod
def validate_property_A(cls, v):
    """Validate new_site_property value."""
    if v is not None and (v < -10.0 or v > 10.0):
        raise ValueError(f"property_A must be between -10 and 10, got {v}")
    return v
```

### Step 2: Add Computed Field for Array Access

If the property should be accessible as an array (which is the case for site-based properties), add a computed field in the `StructureBaseModel` class in `src/aiida_atomistic/data/structure/models.py`. In this case, we can define the `property_A_array` computed field:

```python
@computed_field(
    json_schema_extra={
        "store_in": "repository",      # Decide the storage backend, default is "db" -- see below
        "singular_form": "property_A"  # Maps plural → singular, i.e. the corresponding Site field (REQUIRED)
    }
)
@property
def property_A_array(self) -> t.Optional[np.ndarray]:
    """
    Return the property_A values of all sites as a numpy array.

    Returns:
        np.ndarray: An array of values corresponding to each site, or None if not set.
    """
    if all(site.property_A is None for site in self.sites):
        return None

    # Get default value from Site field metadata, exception if it's not defined:
    default_value = Site.get_default_values().get('property_A')

    return np.array([
        site.property_A if site.property_A is not None
        else default_value
        for site in self.sites
    ])
```

:::{important}
**Key Points:**

1. **Check for all None first**: If all sites have `property_A=None`, return `None` for the entire array. This indicates the property is truly undefined for the structure.

2. **Use `Site.get_default_values()`**: Instead of hardcoding defaults, retrieve them from the Site field metadata:
   ```python
   default_value = Site.get_default_values().get('property_A', 0.0)
   ```
   This keeps the default value definition in one place (the Site field's `json_schema_extra`).

3. **Always include `singular_form`**: This metadata is **required** for loading structures from the database. See the metadata explanation below.
:::

#### Step 3: storage backend decision and additional computed fields for efficient querying

The `json_schema_extra` parameter controls where  the property is stored. Under the key `store_in`, it is possible to define:

- `db`: the default location, which allows the property to be queried from the database
- `repository`: store the property in the repository, i.e. not queriable. Particularly suited for long array and which does not makes sense to query, like positions, charges, magmoms.

In the case you choose to store the property in the repository, it can be useful to define some additional computed field which can be stored in the database, to allow efficient querying of useful information.
For example, we might be interested in the maximum and minimum values of property_A:

**Examples:**

```python
# Statistical computed fields for querying
@computed_field(json_schema_extra={, "store_in": "db", "statistic": "max"})
@property
def max_charge(self) -> t.Optional[float]:
    """Maximum charge value across all sites."""
    if self.charges is None:
        return None
    return float(np.max(self.charges))

# Statistical computed fields for querying
@computed_field(json_schema_extra={, "store_in": "db", "statistic": "min"})
@property
def max_charge(self) -> t.Optional[float]:
    """Maximum charge value across all sites."""
    if self.charges is None:
        return None
    return float(np.min(self.charges))
```

See [Storage Backends](../in_depth/storage_backends.md) for more details.



### Step 4: Add Setter Method

Add a setter method in `src/aiida_atomistic/data/structure/setter_mixin.py`:

```python
def set_property_A_array(self, values: t.Union[list, np.ndarray]):
    """
    Set the property_A values for all sites.

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
        self.properties.sites[i].property_A = float(value)
```

### Step 5: Add Getter Method

Add a getter method in `src/aiida_atomistic/data/structure/getter_mixin.py`:

```python
def get_property_A_array(self) -> t.Optional[np.ndarray]:
    """
    Get the new_site_property values for all sites.

    Returns:
        np.ndarray: Array of values, or None if not set.
    """
    return self.properties.property_A_array
```

### Step 6: Add Remove Method

Add a remove method in `src/aiida_atomistic/data/structure/setter_mixin.py`:

```python
def remove_property_A_array(self):
    """
    Remove property_A from all sites.
    """

    self.remove_property('property_A')
        return
```

### Step 7: Add Tests

Create tests in `tests/data/test_models.py` or appropriate test file:

```python
def test_property_A():
    """Test property_A."""
    structure_dict = {
        "pbc": [True, True, True],
        "cell": [[3.0, 0, 0], [0, 3.0, 0], [0, 0, 3.0]],
        "sites": [
            {"symbol": "Fe", "position": [0, 0, 0], "property_A": 1.5},
            {"symbol": "Fe", "position": [1.5, 1.5, 1.5], "property_A": 2.3},
        ],
    }

    structure = StructureData(**structure_dict)
    assert np.allclose(structure.properties.property_A_array, [1.5, 2.3])

    # Test setter for mutable
    mutable = StructureBuilder(**structure_dict)
    mutable.set_property_A_array([3.1, 4.2])
    assert np.allclose(mutable.properties.property_A_array, [3.1, 4.2])
```

### Step 8: Update Documentation

Add the property to the documentation:

1. Add to property the corresponding tables collecting all the properties
2. Add usage examples
3. Document any special behavior or constraints

---

### Adding Global Properties

Global properties (like temperature, pressure) follow a simpler pattern than site properties since they don't need array expansion.

Key differences from site properties:
- No need for `"default"` in `json_schema_extra` (no array expansion needed)
- Only need `default=None` in Field definition
- No need for `Site.get_default_values()` in computed fields
- Typically stored in database with `"store_in": "db"` for queryability
- No need for statistics computed fields

As example, let's add a `temperature` property that applies to the entire structure. The steps are:

1. Edit `src/aiida_atomistic/data/structure/models.py`:

```python
class StructureBaseModel(BaseModel):
    # ... existing fields ...

    temperature: t.Optional[float] = Field(
        default=None,  # Indicates "not set"
        ge=0,  # Temperature must be non-negative
        json_schema_extra={
            "store_in": "db",  # Store in database for querying
            "property_type": "global"  # Mark as global property
        },
        description="Temperature in Kelvin"
    )
```

2. Add a setter in `src/aiida_atomistic/data/structure/setter_mixin.py`:

```python
def set_temperature(self, temperature: float):
    """
    Set the temperature for the structure.

    Args:
        temperature: Temperature in Kelvin.

    Raises:
        TypeError: If called on an immutable structure.
        ValueError: If temperature is negative.
    """
    if not isinstance(self, StructureBuilder):
        raise TypeError("Can only set properties on StructureBuilder")

    if temperature < 0:
        raise ValueError("Temperature must be non-negative")

    self.properties.temperature = float(temperature)
```

3. Add a getter in `src/aiida_atomistic/data/structure/getter_mixin.py`:

```python
def get_temperature(self) -> t.Optional[float]:
    """
    Get the temperature of the structure.

    Returns:
        float: Temperature in Kelvin, or None if not set.
    """
    return self.properties.temperature
```

4. Add a remove method in `src/aiida_atomistic/data/structure/setter_mixin.py`:

```python
def remove_temperature(self):
    """
    Remove the temperature property from the structure.
    """
    self.remove_property('temperature')
```
