# Running Calculations

## Introduction

This guide demonstrates how to use aiida-atomistic structures in computational workflows, particularly with **Quantum ESPRESSO** through the `aiida-quantumespresso` plugin. We'll cover the basic `PwBaseWorkChain` for a generic self-consistent field (SCF) calculation.

## Prerequisites

Ensure you have the necessary packages installed:

```bash
pip install aiida-core # for now: `support/atomistic` branch from https://github.com/mikibonacci/aiida-core.git
pip install aiida-pseudo # for now: `atomistic` branch from https://github.com/mikibonacci/aiida-pseudo.git
pip install aiida-quantumespresso # for now: `atomistic ` branch from https://github.com/mikibonacci/aiida-quantumespresso.git
```

And configure your Quantum ESPRESSO code:

```bash
verdi code list  # Check existing codes
verdi code create core.code.installed  # Create new code if needed
```

Finally, install pseudos, if not already done:

```bash
aiida-pseudo install sssp # install the default SSSP/1.3/PBE/efficiency family
```

## Basic SCF WorkChain

```python
from aiida import orm, load_profile
from aiida.engine import run_get_node

from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain
from aiida_atomistic import StructureData

from ase.build import bulk

load_profile()

# Create silicon structure
si_atoms = bulk('Si', 'diamond', a=5.43)
structure = StructureData.from_ase(si_atoms, detect_kinds=True)

print(f"Created structure: {structure.properties.formula}")
print(f"Cell volume: {structure.properties.cell_volume:.2f} Angstrom^3")
print(f"Kinds: {structure.kinds}")
```

**Output:**
```
from aiida import orm, load_profile
from aiida.engine import run_get_node

from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain
from aiida_atomistic import StructureData

from ase.build import bulk

load_profile()

# Create silicon structure
si_atoms = bulk('Si', 'diamond', a=5.43)
structure = StructureData.from_ase(si_atoms, detect_kinds=True)

print(f"Created structure: {structure.properties.formula}")
print(f"Cell volume: {structure.properties.cell_volume:.2f} Angstrom^3")
print(f"Kinds: {structure.kinds}")
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

## Adding `tot_charge` in our input

Here below we show a simple example on how to add(remove) charge to the system, and run again the calculation. We basically load the Atoms object using the `StructureBuilder`, we add charge and we resubmit:

```python
structure = StructureBuilder.from_ase(si_atoms, detect_kinds=True)
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

The `from_builder` methods automatically detects the kinds. It is possible to deactivate this by providing `detects_kinds=False` when invoking the method.

## Next Steps

You now have the tools to run sophisticated calculations with aiida-atomistic! Explore the [API documentation](../reference/index.md) for more advanced features.
