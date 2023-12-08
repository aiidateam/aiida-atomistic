# The StructureData object

Here we present the `StructureData` class and we explain the basics on how to interact with it, to
be used as input and output of simulations. This is an extended implementation of the StructureData implemented in `aiida-core`.

The main new feature of this new implementation is the possibility do define several properties, to be associated to the defined crystal structure.
Among them, we have:

- magnetization
- electronic charge
- system dimensionality, i.e. periodic boundary conditions (PBC)
- hubbard U and V parameters

In principle, some of these properties are related to the single sites/atoms (e.g. hubbard U,V) and some are related to the whole system (e.g. PBC).

<div style="border:2px solid #f7d117; padding: 10px; margin: 10px 0;">
    <strong>Important:</strong> we dropped the kind-base definition of the structure: we only have sites, now. This simplifies the properties defintion and respect the philosophy of a code-agnostic representation of the structure.
</div>

The possibility to have user defined custom properties is discussed in this section (TOBE ADDED).

To explore the available properties in detail, please go to the corresponding page (TOBE ADDED).

## Creation of a StructureData instance

In the following, different ways to create a StructureData instance are shown, starting from a property-free structure (only crystal structure), the simplest one.

### Setting just the crystal structure

As in the old StructureData, it is possible to define just the crystal structure, i.e. the unit cell and the atomic positions. Default unit of lenght is Angstrom.

```python
In [1]: StructureData = DataFactory('atomistic.structure')

In [2]: unit_cell = [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]

In [3]: positions = [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]]

In [4]: symbols = ("Li", "Li")

In [5]: structure = StructureData(cell=unit_cell, positions=positions, symbols=symbols)
```

As shown above, all the informations provided are used in one go, when StructureData instance is created.
This is the only allowed way to initialize a structure.
You can then inspect the structure object:

```python
In [6]: structure.cell
Out[6]: [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]

In [7]: structure.sites
Out[7]: [<Site: 'Li' @ 0.0,0.0,0.0>, <Site: 'Li' @ 1.5,1.5,1.5>]

In [8]: structure.properties.pbc
Out[8]: Pbc(value=(True,True,True))
```

Please note the difference with respect to the `orm.StructureData`: no `kind_name` is defined in the sites attribute. Moreover, the `pbc` property, is always initialized and set to describe a bulk system (i.e. PBC in all the three spatial directions).

The actual value of the property can be accessed via the value attribute: `structure.properties.pbc.value`.

### Setting the crystal structure and properties

Let's suppose we have a 2D structure. In this case, we need to define the PBC consistently.
We should then provide the following information during to the StructureData constructor:

```python
In [9]: data = {
    "unit_cell" : [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 25]],
    "positions" : [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]],
    "symbols" : ("Li", "Li"),
    "properties" : {
        'pbc' : (True,True,False)
    }
}

In [10]: structure = StructureData(**data)

In [11]: structure.properties.pbc
Out[11]: Pbc(value=((True,True,False))
```

The `pbc` property is useful for example during the generation of the k-points mesh. Indeed, the sampling of the BZ along non-periodic directions will be performed only at Gamma.

<div style="border:2px solid #f7d117; padding: 10px; margin: 10px 0;">
    <strong>Important:</strong> system properties have to be provided as key-value pair in a dictionary under the keyword `properties`.
</div>

What if have also the magnetization of each atom and I want my structure to have this information? A new instance of the StructureData has to be generated as follows:

```python
In [12]: data = {
    "unit_cell" : [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 25]],
    "positions" : [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]],
    "symbols" : ("Li", "Li"),
    "properties" : {
        'pbc' : (True,True,False),
        'magnetization': ([0.0,0.0,0.5],[0.0,0.0,-0.5])
    }
}

In [13]: structure = StructureData(**data)

In [14]: structure.properties.magnetization
Out[14]: Magnetization(value=([0.0,0.0,0.5],[0.0,0.0,-0.5]))
```

A consistency check is then performed with respect to the properties provided. Here, for example, a check on the number of magnetization vectors provided and the number of atoms is done.
Units of magnetization are Bohr magnetons. 
TOBE ADDED: See the corresponding page on `magnetization` to have a full description of the property.

## The immutability of the `StructureData` instance and constructors

A crucial aspect of the new `StructureData` is that it is immutable even if the node is not stored, i.e. the API does not support on-the-fly or interactive modifications. This was determined mainly to avoid unexpected 
behaviour coming from a step-by-step defintion of the structure, e.g. incosistencies between properties definitions, which are then not cross-checked again.

One has to define a new `StructureData` instance by scratch.
To make user life simpler, we prodied a `from_structuredata` method, to be used as follows:

```python
In [15]: data_overrides = {
    "unit_cell" : [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]],
    "properties" : {
        'pbc' : (True,True,True),
    }
}

In [16]: new_structure = StructureData.from_structuredata(structure = structure, overrides = data_overrides)

In [17]: new_structure.cell # this is updated with respect to the original structure
Out[17]: [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 3.5]]

In [18]: new_structure.properties.pbc # this is updated with respect to the original structure
Out[18]: Pbc(value=(True,True,True))

In [19]: new_structure.properties.magnetization # this is the same as the original structure 
Out[19]: Magnetization(value=([0.0,0.0,0.5],[0.0,0.0,-0.5]))
```

In practice, the new structure is generated starting from the attributes of the input one, enriched/updated
following the `overrides` input dictionary.

### Different types of costructors

- from_file(cif,xyz,mcif)
- from_ase
- from_pymatgen
- from_structuredata

If some supported property is defined in the ASE of pymatgen objects, it will be parsed on stored. We can always override it: each one of these methods has as additional input parameters the `overrides` one.

## Managing properties inside the `StructureData` object: the `properties` attribute

### List of supported properties

The list of all supported properties can be accessed via the `StructureData.get_available_properties()` classmethod:

```python
In [20]: StructureData.get_available_properties()
Out[20]: ["pbc","magnetization","hubbard","charge"]
```

They can also be inspected using tab completion, even on just the class object (not necessarily the instance object):

```python
In [21]: StructureData.properties. + tab
```

this will provide the tab completion for all supported/available properties, each of them initialized as *None/empty* in the class. 

### List of stored properties

Stored properties of a `StructureData` node can be accessed singularly via tab completion, as seen in the previous subsection, or can be also obtained invoking the `get_defined_properties` method. 

```python
In [22]: structure.get_defined_properties()
Out[22]: {
    "pbc": (True,True,True),
    "magnetization": ([0.0,0.0,0.5],[0.0,0.0,-0.5])
}

In [23]: structure.get_defined_properties("magnetization")
Out[23]: Magnetization(value=([0.0,0.0,0.5],[0.0,0.0,-0.5]))
```

## How to query StructureData nodes

## The `to_*` methods

- to_ase
- to_pymatgen
- to_cif/xyz/mcif...

These methods will also dump the defined properties, whenever it is possible (e.g., magnetization in mcif).

## User defined custom properties