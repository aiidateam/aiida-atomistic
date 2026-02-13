---
myst:
  substitutions:
    README.md of the repository: '`README.md` of the repository'
    aiida-core documentation: '`aiida-core` documentation'
    aiida-atomistic: '`aiida-atomistic`'
---
```{toctree}
:hidden: true

installation_quickstart/quickstart
```

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
:caption: Dev guides

dev_guides/index
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
Create, manipulate, and store atomic structures with property support: magnetic moments, charges, Hubbard parameters and more.
Specifically developed for DFT calculations, molecular dynamics, and high-throughput materials discovery.

[![PyPI version](https://badge.fury.io/py/aiida-atomistic.svg)](https://badge.fury.io/py/aiida-atomistic)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/aiida-atomistic.svg)](https://pypi.python.org/pypi/aiida-atomistic)
[![Build Status](https://github.com/aiidateam/aiida-atomistic/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aiidateam/aiida-atomistic/actions)
[![Docs status](https://readthedocs.org/projects/aiida-atomistic/badge)](http://aiida-atomistic.readthedocs.io/)

______________________________________________________________________

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} {fa}`rocket;mr-1` Getting started
:text-align: center
:shadow: md

Quick start guide.

+++

```{button-ref} installation_quickstart/quickstart
:ref-type: doc
:click-parent:
:expand:
:color: primary
:outline:

To the quick start guide
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
