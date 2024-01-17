# The `pbc` property

The `pbc` property describes the periodic boundary conditions for a periodic system. 
It should be provided as a tuple of three boolean values:

```python
In [1]: StructureData = DataFactory('atomistic.structure')

In [2]: data = {
    "unit_cell" : [[3.5, 0.0, 0.0], [0.0, 3.5, 0.0], [0.0, 0.0, 25]],
    "positions" : [[0.0, 0.0, 0.0],[1.5, 1.5, 1.5]],
    "symbols" : ("Li", "Li"),
    "properties" : {
        'pbc' : (True,True,False),
    }
}

In [3]: structure = StructureData(**data)

In [4]: structure.properties.pbc
Out[4]: Pbc(value=(True,True,False))
```

in the above example we are considering a 2D system, where the third direction in space is not periodic.
Note that if no `pbc` key is found in the properties dictionary, then it will default to `(True, True, True)`. 
The `pbc` property is stored as the `Pbc` class.
It is possible to access the value of the property in two ways:

```python
In [5]: structure.properties.pbc.value
Out[5]: (True,True,False)

In [6]: structure.pbc
Out[6]: (True,True,False)
```

the second way, i.e. the direct access via `structure.pbc`, is provided in order to support backward compatibility.