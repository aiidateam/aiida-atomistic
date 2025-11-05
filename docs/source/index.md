---
myst:
  substitutions:
    README.md of the repository: '`README.md` of the repository'
    aiida-core documentation: '`aiida-core` documentation'
    aiida-atomistic: '`aiida-atomistic`'
---

```{toctree}
:hidden: true

installation
tutorials/index
```

```{toctree}
:hidden: true
:caption: How to

how_to/index
```

```{toctree}
:hidden: true
:caption: In-Depth Guides

in_depth/index
```

```{toctree}
:hidden: true
:caption: Reference
reference/api/index
reference/cli/index
```

# AiiDA Atomistic

An AiiDA plugin package providing data classes for atomistic simulations.
Create, manipulate, and store atomic structures with enhanced property support, magnetic moments, charges, Hubbard parameters, and automatic data provenance provided by AiiDA.
Specifically developed for DFT calculations, molecular dynamics, and high-throughput materials discovery.

[![PyPI version](https://badge.fury.io/py/aiida-atomistic.svg)](https://badge.fury.io/py/aiida-atomistic)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/aiida-atomistic.svg)](https://pypi.python.org/pypi/aiida-atomistic)
[![Build Status](https://github.com/aiidateam/aiida-atomistic/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aiidateam/aiida-atomistic/actions)
[![Docs status](https://readthedocs.org/projects/aiida-atomistic/badge)](http://aiida-atomistic.readthedocs.io/)

______________________________________________________________________

## Key Features

- **Enhanced StructureData**: Advanced atomistic structure representation with comprehensive property support
- **Magnetic Properties**: Full support for collinear and non-collinear magnetic moments
- **Electronic Properties**: Charges, Hubbard parameters, and custom electronic properties
- **Kinds System**: Efficient grouping of atoms with identical properties for optimized storage
- **Multiple Formats**: Seamless import/export with ASE, pymatgen, CIF, MCIF, and legacy AiiDA formats
- **Backward Compatible**: Drop-in replacement for legacy AiiDA StructureData


::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} {fa}`rocket;mr-1` Getting started
:text-align: center
:shadow: md

Instructions to install, configure and setup the plugin package.

+++

```{button-ref} installation
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the installation guides
```
:::

:::{grid-item-card} {fa}`info-circle;mr-1` Tutorials
:text-align: center
:shadow: md

Easy examples to take the first steps with the enhanced StructureData.

+++

```{button-ref} tutorials/index
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the tutorials
```
:::

:::{grid-item-card} {fa}`tools;mr-1` How-to guides
:text-align: center
:shadow: md

Step-by-step guides for common tasks and workflows.

+++

```{button-ref} how_to/index
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the how-to guides
```
:::

:::{grid-item-card} {fa}`book;mr-1` In-depth guides
:text-align: center
:shadow: md

In-depth explanations of concepts, implementation and advanced topics.

+++

```{button-ref} in_depth/index
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the in-depth guides
```
:::
::::

## Quick Start

Create and manipulate advanced atomistic structures:

```python
from aiida_atomistic.data.structure import StructureData
import numpy as np

# Create structure with magnetic properties
sites = [
    {
        "symbol": "Fe",
        "position": np.array([0.0, 0.0, 0.0]),
        "magmom": np.array([0.0, 0.0, 2.2]),
        "charge": 0.5,
        "kind_name": "Fe1"
    },
    {
        "symbol": "O",
        "position": np.array([1.0, 1.0, 1.0]),
        "charge": -1.0,
        "kind_name": "O1"
    }
]

structure = StructureData(
    cell=np.eye(3) * 4.0,
    pbc=[True, True, True],
    sites=sites
)

# Access properties
print(f"Formula: {structure.formula}")
print(f"Magnetic moments: {structure.magmoms}")
print(f"Total magnetization: {structure.total_magnetization}")
```

### Import from Popular Formats

```python
# From ASE
from ase.build import bulk
ase_atoms = bulk('Fe', 'bcc', a=2.87)
structure = StructureData.from_ase(ase_atoms)

# From pymatgen
from pymatgen.core import Structure
pmg_struct = Structure.from_file('structure.cif')
structure = StructureData.from_pymatgen(pmg_struct)

# From CIF/MCIF files
structure = StructureData.from_file('magnetic_structure.mcif')

# From legacy AiiDA StructureData
legacy_structure = orm.load_node(pk)
new_structure = legacy_structure.to_atomistic()
```

## What's New in aiida-atomistic

### Enhanced Property Support
- **Magnetic moments**: Full vector magnetic moments with collinear/non-collinear support
- **Electronic charges**: Partial charges and oxidation states
- **Hubbard parameters**: Native support for DFT+U calculations
- **Custom properties**: Extensible framework for additional atomic properties

### Efficient Storage with Kinds
- **Automatic grouping**: Atoms with identical properties are automatically grouped into "kinds"
- **Optimized storage**: Significant space savings for large structures with repeated atom types
- **Performance**: Faster loading and manipulation of structures with many atoms

### Modern Python Architecture
- **Pydantic models**: Type-safe, validated data structures
- **Immutable by design**: Prevents accidental data corruption
- **Caching**: Automatic caching of expensive computations
- **Extensible**: Easy to add new properties and validation rules

## Migration from Legacy StructureData

aiida-atomistic provides seamless migration tools:

```python
# Convert existing structures
legacy_structure = orm.load_node(pk)
new_structure = legacy_structure.to_atomistic()

# Use in existing workflows
from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain
builder = PwBaseWorkChain.get_builder_from_protocol(
    code=code,
    structure=new_structure,  # Drop-in replacement
    protocol="fast"
)
```

See our [migration guide](howto/migration/index.md) for detailed instructions.

## Advanced Features

### Mutable Structures for Construction
```python
from aiida_atomistic.data.structure import StructureBuilder

# Create mutable structure for building
mutable = StructureBuilder(cell=cell, pbc=pbc)

# Add atoms with properties
mutable.append_atom(
    symbol="Fe",
    position=[0, 0, 0],
    magmom=[0, 0, 2.2],
    charge=0.5
)

# Automatic kinds generation
mutable.generate_kinds(tolerance={'charge': 1e-3})

# Convert to immutable for storage
structure = StructureData.from_builder(mutable)
```

### Integration with Quantum ESPRESSO
```python
# Hubbard parameters for DFT+U
mutable.initialize_onsites_hubbard('Fe1', '3d', 4, 'U')

# Export Hubbard card for QE
from aiida_atomistic.data.structure.hubbard_qe_utils import HubbardUtils
hubbard_card = HubbardUtils(structure).get_hubbard_card()
```

## Performance Benefits

Benchmark comparisons show significant improvements:

- **Storage efficiency**: Up to 70% reduction in database size for structures with repeated atoms
- **Loading speed**: 2-5x faster structure loading from database
- **Memory usage**: Reduced memory footprint through kinds-based storage
- **Validation**: Cached validation prevents redundant checks

## How to cite

If you use this plugin for your research, please cite the following work:

> Sebastiaan. P. Huber, Spyros Zoupanos, Martin Uhrin, Leopold Talirz, Leonid Kahle, Rico Häuselmann, Dominik Gresch, Tiziano Müller, Aliaksandr V. Yakutovich, Casper W. Andersen, Francisco F. Ramirez, Carl S. Adorf, Fernando Gargiulo, Snehal Kumbhar, Elsa Passaro, Conrad Johnston, Andrius Merkys, Andrea Cepellotti, Nicolas Mounet, Nicola Marzari, Boris Kozinsky, and Giovanni Pizzi, [*AiiDA 1.0, a scalable computational infrastructure for automated reproducible workflows and data provenance*](https://doi.org/10.1038/s41597-020-00638-4), Scientific Data **7**, 300 (2020)

> Martin Uhrin, Sebastiaan. P. Huber, Jusong Yu, Nicola Marzari, and Giovanni Pizzi, [*Workflows in AiiDA: Engineering a high-throughput, event-based engine for robust and modular computational workflows*](https://doi.org/10.1016/j.commatsci.2020.110086), Computational Materials Science **187**, 110086 (2021)

## Acknowledgements

We acknowledge support from:

:::{list-table}
:widths: 60 40
:class: logo-table
:header-rows: 0

* - The [NCCR MARVEL](http://nccr-marvel.ch/) funded by the Swiss National Science Foundation.
  - ![marvel](images/MARVEL.png)
* - The EU Centre of Excellence ["MaX – Materials Design at the Exascale"](http://www.max-centre.eu/) (Horizon 2020 EINFRA-5, Grant No. 676598).
  - ![max](images/MaX.png)
* - The [swissuniversities P-5 project "Materials Cloud"](https://www.materialscloud.org/swissuniversities)
  - ![swissuniversities](images/swissuniversities.png)

:::

[aiida]: http://aiida.net
[aiida-core documentation]: https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html
[aiida-atomistic]: https://github.com/aiidateam/aiida-atomistic
