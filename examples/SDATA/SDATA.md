Storing the values of the properties in the repository, so we efficiently store them. we can use .npy files.
- Avoids storing large or sparse arrays in the DB.
- .npy is highly compact and fast to load for numerical arrays.


We can decide (store_mode=full/compact/compression) to store the properties both site- or kind-based, the second one being more compact.
 - of course, there should be some validation, in case we also provide kind based... for consistency.
 - when we update a mutable structure, we will not validate kinds. but we will do it when we store, if we store kind-wise.
 - we can even do a default check that, if the kinds generation does not change the value of any site-property, we can store kind-based. like automatic compression.
We will have functions and methods to generate automatically the kinds, if we want.
This will not affect user experience as when we retrieve the properties, we can see them site-wise.
If kinds are defined, also kind-wise. Otherwise, kinds can be generated on-the-fly both in the plugins both from the SDATA, to check.

In the db, we store stuff that can be easily queried: properties defined, max-min values of properties, and properties which are global like pbc, cell, tot_charge ... alloy...
Even weights now can be stored in the repository, we can just then put "is_alloy" in the db... so we know... TBD

So, the DB properties are, apart the global ones, properties derived from the ones in the repository. This would be mostly computed_fields?

Then how do we do with the mutable? In principle, we can just put arrays and it's fine.

The idea is then the build sites/kinds from npy when we load, and do the viceversa when we store.

### np arrays immutability

```python
import numpy as np

arr = np.array([1, 2, 3])
arr.flags.writeable = False

try:
    arr[0] = 10  # This will raise a ValueError
except ValueError as e:
    print("Array is immutable:", e)
```
Limitations: The immutability is shallow. If the array is part of a larger mutable structure, the structure itself can still be modified.

### np array files compressed or not

check np.savez and its compressed version (which is slower):
```python
np.savez("data.npz", magmom=magmom_array, charge=charge_array)
np.savez_compressed("data_compressed.npz", magmom=magmom_array, charge=charge_array)
```

maybe they can be used to store the properties in the repository.
Compressed files separately for site/kind properties, site-pair properties, global... or anyway stuff we don't want to query.

### Row-modeled tables and EAV

Classical tables, each line is a site and the columns are all the properties (NULL if not defined).
Instead, EAV is flexible schema where basically the first column is the entity (it can be repeated),
the second column is the attribute (charge, or and magmom) and the third one is the value. This is useful
to represents sparse data. HOWEVER, not sure it is easy for use:
- we need then to iterate over and distribute the propeties
- if we use npy, I don't know about heterogeneous data... not really efficient I would say.
- if we use json, maybe it can work, but maybe it's better to have an npy for each property.

Solution: use a single EAV for each property.

So, an .npy file for each property, one column with the site/kind based, and one for the value of the property.

#### Example of repository:

```shell
repository/
├── magmom.npy
├── charge.npy
├── oxidation.npy
└── metadata.json  # (optional, it should be in the BaseModel of the class object - see metadata section)
```


THE REPOSITORY CAN CONTAIN DIFFERENT INFO FOR DIFFERENT STRUCTURES. I MEAN, IN DIFFERENT FORMATS(SITES, KINDS....)



#### Metadata
in EAV, metadata tables are crucial. Mostly, these are attribute metadata, used for validation, presentation and grouping (https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model#Information_captured_in_metadata). These can be the pydantic Models of each property... or anyway the whole
BaseModel which encodes all (so, one metadata table, basically). Also, dependency metadata and computation, as well as complex validation.

-> populate the npy tables using sites or kinds or the mutable object.

```json
{
  "magmom": {
    "target": "site",
    "units": "µB",
    "dtype": "float",
    "components": 3,
    "shape": [3],
    "description": "3D magnetic moment vector per site"
  },
  "charge": {
    "description": "Atomic charge from Bader analysis",
    "units": "e",
    "data_type": "float",
    "required": false,
    "default_value": null,
    "source": "Bader analysis"
  }
}
```

So, magmom would be a 3D quantity:

```python
np.array([
    [0, 1.0, 0.0, 0.0],  # site 0: [1.0, 0.0, 0.0]
    [2, 0.0, 1.0, 0.0],  # site 2: [0.0, 1.0, 0.0]
    [3, 0.1, 0.2, 0.3]   # site 3: [0.1, 0.2, 0.3]
])
```

for tensors or matrixes, I can flatten them.

#### Handling different data types within npy

The main issue in using .npy is if we need to store non-numerical types like strings.
Handling string-valued properties in NumPy .npy files requires a bit of care, since NumPy arrays are primarily optimized for numerical data. But anyway it is possible:

```python
import numpy as np

data = np.array([
    (0, "surface"),
    (1, "bulk"),
    (3, "defect")
], dtype=[("index", "i4"), ("value", "U20")])  # U20 = Unicode string, max length 20

np.save("site_labels.npy", data)
```

In this case, metadata can be:

```json
"site_labels": {
  "target": "site",
  "dtype": "str",
  "description": "Label for each site (e.g., surface, defect)",
  "allowed_values": ["surface", "bulk", "defect"]
}
```

Maybe we can use a mixed approach, for some of them we can use a json-based:

```json
[
  {"index": 0, "value": "surface"},
  {"index": 1, "value": "bulk"},
  {"index": 2, "value": "vacancy"}
]
```

and for some others we can use the .npy way? It is just much faster than json like, I think.

### Storage in the repository

- Each property is a (N,M) array with site index the first column, value of the property in the other columns.
- if we store kind based, we will find the "kind" property in the repository, so we know that we need to parse in a given way.

For site-related properties, I expect this format:

```python
data["charge"] = np.array([
  [0, +1]
  [2, -1]
])
```

Where, in this case, the first and the third sites has charge defined and different from the default (0).
So this will be used to build the StructureData.

If we have also kinds defined, the analogous of the above will be:

```python
data["charge"] = np.array([
    ["Fe1", +1]
    ["Fe3", -1]
  ]
)

data["kinds"] = np.array([
    ["Fe1",[0]],
    ["Fe2", [1,4]],
    ["Fe3", [2]]
  ],
  , dtype=[("index", "U20"), ("value", "i4")]
)

if "kinds" in data...
```

- TODO: check that it is efficient to store kinds (literal plus list of indexes) in npy and not in json. and check that we cannot somehow store in a smarter way, if we have kinds.

### Loading back the properties

The question is: do we want our python object to be site based anyway? or we put it as kind based, if kinds are defined? I think we should have only one way, i.e. the site based.
Maybe we can make an exception if then we risk to have memory overloading, but I don't think it will be the case so often. I just need a mapping the uncompress the properties from kinds to sites.
Then the implementation should be already there.

### STEPS

#### 1. Constructor

From input, we allow basically three ways:
- properties as list, each element is the property for a given site
- list of site dictionaries
- list kinds dictionaries + positions list

Then, we build the python object in a unique way, otherwise it will be a problem for the API.
The class will hold data in a site-wise manner.
Kinds can be there, or can be generated on the fly by plugins or by the user - the method with give a new instance of the object with the kinds,
it will now update the python object (even if it is the mutable case).

NB: the validation of kinds will be done only at the storage moment, not when you are still modifying the StructureData mutable - of course we will have a method for validation, that can be executed also beforehand by the user to check - this is also useful for the on the fly generation, if we need to have a limited number of kinds, as in the QE case.

#### 2. Storage in the repository and in the db

We store the properties in different ways, as we can have a full site based, or kind based, which is more compact.
Of course, when we store kind based, we need to do some validation of the kind groups.

The db instead, needs to be populated in a unique way, as we want to query and we need to be consistent wrt different StructureData nodes.
In the db we put stuff which has fixed dimension and is useful to query, plus some information on the properties we store in the repository, like
the max charge, if there is charge, if alloy, and so on... all stuff that will not give problems if we have several hundreds or thousands of atoms.


#### 3. In plugins

If we generate kinds on the fly in plugins, we need to be sure that mappings are consistent, like for pseudos... we need to accept also a site-based definition of pseudos


### StructureDataMutable?

The implementation will not change actually, apart that we now have arrays for the properties, I would say. It's just easier to deal with.
We DO NOT TEST KINDS until we store the structure or we call a validation method (which will be called when we try to store).
