# Quick Start

Here you will first install the aiida-atomistic package, then generate your first `StructureData`.

## Installation

### Prerequisites

Before installing aiida-atomistic, ensure you have:

- Python 3.9 or later
- AiiDA core installed and configured
- A working AiiDA profile

If you don't have AiiDA set up yet, follow the [AiiDA installation guide](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html).

### From PyPI (Not ready)

```text
pip install aiida-atomistic
```

### From Source (Development)

```text
git clone https://github.com/aiidateam/aiida-atomistic.git
cd aiida-atomistic
pip install -e .
```

### Verify Installation

Test that everything is working correctly:

```python
from aiida import load_profile
load_profile()

from aiida_atomistic.data.structure import StructureData
print("✅ aiida-atomistic installed successfully!")
```

## Quick structure generation

It is possible to initialize a `StructureData` instance from the corresponding ASE `Atoms` object:

```python
from ase.build import bulk
ase_atoms = bulk('Fe', 'bcc', a=2.87)
structure = StructureData.from_ase(ase_atoms)
structure
```

```
<StructureData: uuid: 529cac23-f00a-458b-af93-d6c858f8d87c (unstored)>
  | formula: Fe, sites: 1, dimensionality: 3D, V=11.82 A^3 |
 Sites: symbol='Fe' position=array([0., 0., 0.]) mass=55.845 charge=None magmom=None magnetization=None weight=None kind_name=None
```

We can also inspect all the properties:

```python
structure.properties
```

```
StructureModel({'cell': [[-1.435, 1.435, 1.435],
          [1.435, -1.435, 1.435],
          [1.435, 1.435, -1.435]],
 'cell_volume': 11.8199515,
 'charges': None,
 'custom': None,
 'dimensionality': {'dim': 3, 'label': 'volume', 'value': 11.8199515},
 'formula': 'Fe',
 'has_vacancies': False,
 'hubbard': {'formulation': 'dudarev',
             'parameters': [],
             'projectors': 'ortho-atomic'},
 'is_alloy': False,
 'kind_names': None,
 'kinds': None,
 'magmoms': None,
 'magnetizations': None,
 'masses': array([55.845]),
 'max_charge': None,
 'max_magmom': None,
 'max_magnetization': None,
 'min_charge': None,
 'min_magmom': None,
 'min_magnetization': None,
 'n_sites': 1,
 'pbc': [True, True, True],
 'positions': array([[0., 0., 0.]]),
 'sites': [{'charge': None,
            'kind_name': None,
            'magmom': None,
            'magnetization': None,
            'mass': 55.845,
            'position': [0.0, 0.0, 0.0],
            'symbol': 'Fe',
            'weight': None}],
 'symbols': ['Fe'],
 'tot_charge': None,
 'tot_magnetization': None,
 'weights': None})
```

In case we want to add a property after the creation, we can first pass through the `StructureBuilder`:

```python
from aiida_atomistic.data.structure import StructureBuilder

builder = StructureBuilder.from_ase(ase_atoms)
# alternatively builder = structure.to_builder()

builder.set_magmoms([[0, 0, 2.2]])

structure = StructureData.from_builder(builder)
structure.properties.magmoms
```

```
array([[0. , 0. , 2.2]])
```

### Backward-compatibility

We can initialize a `StructureData` or a `StructureBuilder` instance from an old `orm.StructureData` object:

```python
from aiida.orm import StructureData as LegacyStructureData

legacy = LegacyStructureData(ase=ase_atoms)
structure = legacy.to_atomistic()
```
