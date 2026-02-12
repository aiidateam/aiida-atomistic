# Running Calculations

## Introduction

This guide demonstrates how to use aiida-atomistic structures in computational workflows, particularly with **Quantum ESPRESSO** through the `aiida-quantumespresso` plugin. We'll cover the basic `PwBaseWorkChain` for a generic self-consistent field (SCF) calculation.

## Prerequisites

Ensure you have the necessary packages and codes installed, which you can verify by following the corresponding [installation guide](https://aiida-quantumespresso.readthedocs.io/en/stable/get_started/installation.html).

:::{important}
For now, please install these versions of the following packages:
- aiida-core: dev/atomistic branch from https://github.com/mikibonacci/aiida-core.git
- aiida-pseudo: dev/atomistic branch from https://github.com/mikibonacci/aiida-pseudo.git
- aiida-quantumespresso: dev/atomistic branch from https://github.com/mikibonacci/aiida-quantumespresso.git
:::

If not already done, remember to install the `sssp` pseudopotentials:

```bash
aiida-pseudo install sssp # install the default SSSP/1.3/PBE/efficiency family
```

## Preparing and submitting a basic `PwBaseWorkChain`

If you are new to the `PwBaseWorkChain`, please follow the corresponding [tutorial](https://aiida-quantumespresso.readthedocs.io/en/stable/get_started/quick_start.html).

```python
from aiida import orm, load_profile
from aiida.engine import run_get_node

from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain
from aiida_atomistic import StructureData

from ase.build import bulk

load_profile()

# Create silicon structure
si_atoms = bulk('Si', 'diamond', a=5.43)
structure = StructureData.from_ase(si_atoms)

print(f"Created structure: {structure.properties.formula}")
print(f"Cell volume: {structure.properties.cell_volume:.2f} Angstrom^3")
print(f"Kinds: {structure.properties.kind_names}")
```

**Output:**
```
Created structure: Si2
Cell volume: 40.03 Angstrom^3
Kinds: ['Si', 'Si']
```

As you can see, we detected kinds (from the ASE `atom` tags) and we have them defined in our StructureData. This is needed as Quantum ESPRESSO works **only** with kinds.

Then, we can initialise the WorkChain instance and run the calculation:

```python
builder = PwBaseWorkChain.get_builder_from_protocol(
    code=orm.load_code("pw-qe-7.4@localhost"),
    structure=structure,
    protocol="moderate",
    overrides={
        "pseudo_family": "SSSP/1.3/PBE/efficiency",
    }
)

run = run_get_node(builder)
```

**Output:**
```
09/08/2025 05:21:51 PM <79134> aiida.orm.nodes.process.workflow.workchain.WorkChainNode: [REPORT] [13671|PwBaseWorkChain|run_process]: launching PwCalculation<13676> iteration #1
09/08/2025 05:22:11 PM <79134> aiida.orm.nodes.process.workflow.workchain.WorkChainNode: [REPORT] [13671|PwBaseWorkChain|results]: work chain completed after 1 iterations
09/08/2025 05:22:11 PM <79134> aiida.orm.nodes.process.workflow.workchain.WorkChainNode: [REPORT] [13671|PwBaseWorkChain|on_terminated]: remote folders will not be cleaned
```

## Adding `tot_charge` in our calculation

Here below we show a simple example on how to add(remove) charge to the system, and run again the calculation. We basically load the Atoms object using the `StructureBuilder`, we add charge and we resubmit:

```python
structure = StructureBuilder.from_ase(si_atoms)
structure.set_tot_charge(1.0)

builder = PwBaseWorkChain.get_builder_from_protocol(
    code=orm.load_code("pw-qe-7.4@localhost"),
    structure=StructureData.from_builder(structure),
    protocol="moderate",
    overrides={
        "pseudo_family": "SSSP/1.3/PBE/efficiency",
    }
)

run = run_get_node(builder)
````

**Output:**
```
11/04/2025 05:48:46 PM <42782> aiida.orm.nodes.process.workflow.workchain.WorkChainNode: [REPORT] [13784|PwBaseWorkChain|run_process]: launching PwCalculation<13789> iteration #1
11/04/2025 05:49:09 PM <42782> aiida.orm.nodes.process.workflow.workchain.WorkChainNode: [REPORT] [13784|PwBaseWorkChain|results]: work chain completed after 1 iterations
11/04/2025 05:49:10 PM <42782> aiida.orm.nodes.process.workflow.workchain.WorkChainNode: [REPORT] [13784|PwBaseWorkChain|on_terminated]: remote folders will not be cleaned
```

You can verify that the `tot_charge` was indeed set in the input file of the `pw.x` calculation:

```shell
verdi calcjob inputcat 13789 | grep tot_charge
```

**Output:**
```
tot_charge =   1.0000000000d+00
```

Full explanation on how to set all the properties and automatically detect kinds, is contained in the How to sections.
