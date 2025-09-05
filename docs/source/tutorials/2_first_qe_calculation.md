# Running Calculations

## Introduction

This guide demonstrates how to use aiida-atomistic structures in computational workflows, particularly with **Quantum ESPRESSO** through `aiida-quantumespresso`. We'll cover basic calculations, magnetic systems, and automated workflows.

## Prerequisites

Ensure you have the necessary packages installed:

```bash
pip install aiida-quantumespresso
verdi quicksetup  # If you haven't set up AiiDA yet
```

And configure your Quantum ESPRESSO code:

```bash
verdi code list  # Check existing codes
verdi code create core.code.installed  # Create new code if needed
```

## Basic SCF Calculation

### Setting Up a Simple Structure

```python
from aiida import orm, load_profile
from aiida_atomistic.data.structure import StructureData
from aiida_quantumespresso.calculations.pw import PwCalculation
from aiida_quantumespresso.data.pseudos import PseudoDojoV02

load_profile()

# Create silicon structure
from ase.build import bulk
si_atoms = bulk('Si', 'diamond', a=5.43)
structure = StructureData.from_ase(si_atoms)

print(f"Created structure: {structure.properties.formula}")
print(f"Cell volume: {structure.properties.cell_volume:.2f} Ų")
```

### Preparing Calculation Inputs

```python
from aiida.engine import submit

# Get pseudopotentials
pseudo_family = orm.load_group('SSSP/1.3/PBE/efficiency')
pseudos = pseudo_family.get_pseudos(structure=structure)

# Define calculation parameters
parameters = {
    'CONTROL': {
        'calculation': 'scf',
        'restart_mode': 'from_scratch',
        'outdir': './out/',
        'pseudo_dir': './pseudo/',
    },
    'SYSTEM': {
        'ecutwfc': 30.0,
        'ecutrho': 240.0,
        'degauss': 0.02,
        'smearing': 'gaussian',
        'occupations': 'smearing',
    },
    'ELECTRONS': {
        'conv_thr': 1.0e-8,
        'mixing_beta': 0.7,
    }
}

# Define k-points
kpoints = orm.KpointsData()
kpoints.set_kpoints_mesh([4, 4, 4])

# Define metadata
metadata = {
    'options': {
        'max_wallclock_seconds': 1800,
        'resources': {
            'num_machines': 1,
            'num_mpiprocs_per_machine': 4,
        }
    }
}

# Prepare inputs
inputs = {
    'code': orm.load_code('pw@localhost'),  # Adjust to your code label
    'structure': structure,
    'kpoints': kpoints,
    'pseudos': pseudos,
    'parameters': orm.Dict(dict=parameters),
    'metadata': metadata,
}

print("Calculation inputs prepared")
```

### Submitting the Calculation

```python
# Submit the calculation
calculation = submit(PwCalculation, **inputs)
print(f"Submitted calculation with PK: {calculation.pk}")

# Monitor progress
print(f"Calculation state: {calculation.process_state}")
```

## Magnetic Calculations

### Collinear Magnetic System

```python
# Create magnetic structure (Iron)
from ase.build import bulk
fe_atoms = bulk('Fe', 'bcc', a=2.87)
structure = StructureData.from_ase(fe_atoms)

# Add magnetic moments
from aiida_atomistic.data.structure import StructureDataMutable
mutable = StructureDataMutable.from_ase(fe_atoms)

for site in mutable.sites:
    site.moment = [0.0, 0.0, 2.2]  # 2.2 µB along z

magnetic_structure = StructureData.from_mutable(mutable)

# Magnetic calculation parameters
magnetic_parameters = {
    'CONTROL': {
        'calculation': 'scf',
        'restart_mode': 'from_scratch',
    },
    'SYSTEM': {
        'ecutwfc': 40.0,
        'ecutrho': 320.0,
        'degauss': 0.02,
        'smearing': 'gaussian',
        'occupations': 'smearing',
        'nspin': 2,  # Enable spin polarization
        'starting_magnetization': {
            'Fe': 0.5,  # Starting magnetization for Fe
        }
    },
    'ELECTRONS': {
        'conv_thr': 1.0e-8,
        'mixing_beta': 0.7,
    }
}

# Update inputs for magnetic calculation
magnetic_inputs = inputs.copy()
magnetic_inputs['structure'] = magnetic_structure
magnetic_inputs['parameters'] = orm.Dict(dict=magnetic_parameters)

print("Prepared magnetic calculation")
```

### Non-Collinear Magnetism

```python
# Non-collinear magnetic parameters
noncollinear_parameters = {
    'CONTROL': {
        'calculation': 'scf',
    },
    'SYSTEM': {
        'ecutwfc': 40.0,
        'ecutrho': 320.0,
        'degauss': 0.02,
        'smearing': 'gaussian',
        'noncolin': True,  # Enable non-collinear magnetism
        'lspinorb': True,  # Include spin-orbit coupling
        'starting_magnetization': {
            'Fe': 0.5,
        },
        # Starting magnetic moment directions
        'angle1': [0.0],  # Theta angle
        'angle2': [0.0],  # Phi angle
    },
    'ELECTRONS': {
        'conv_thr': 1.0e-8,
    }
}

print("Configured non-collinear magnetism")
```

## Using WorkChains

### Basic SCF WorkChain

```python
from aiida_quantumespresso.workflows.pw.base import PwBaseWorkChain

# Use the base workchain for better error handling
workchain_inputs = {
    'pw': {
        'code': orm.load_code('pw@localhost'),
        'structure': structure,
        'pseudos': pseudos,
        'parameters': orm.Dict(dict=parameters),
        'kpoints': kpoints,
        'metadata': {
            'options': {
                'max_wallclock_seconds': 1800,
                'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 4},
            }
        }
    }
}

# Submit workchain
workchain = submit(PwBaseWorkChain, **workchain_inputs)
print(f"Submitted workchain with PK: {workchain.pk}")
```

### Relaxation WorkChain

```python
from aiida_quantumespresso.workflows.pw.relax import PwRelaxWorkChain

# Relaxation parameters
relax_parameters = parameters.copy()
relax_parameters['CONTROL']['calculation'] = 'vc-relax'
relax_parameters['CONTROL']['forc_conv_thr'] = 1.0e-4
relax_parameters['CONTROL']['etot_conv_thr'] = 1.0e-6

# Ion dynamics
relax_parameters['IONS'] = {
    'ion_dynamics': 'bfgs',
}

# Cell dynamics
relax_parameters['CELL'] = {
    'cell_dynamics': 'bfgs',
    'press_conv_thr': 0.5,
}

# Relaxation inputs
relax_inputs = {
    'base': {
        'pw': {
            'code': orm.load_code('pw@localhost'),
            'structure': structure,
            'pseudos': pseudos,
            'parameters': orm.Dict(dict=relax_parameters),
            'kpoints': kpoints,
            'metadata': {
                'options': {
                    'max_wallclock_seconds': 3600,
                    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 4},
                }
            }
        }
    },
    'relaxation_scheme': orm.Str('vc-relax'),
}

# Submit relaxation
relax_wc = submit(PwRelaxWorkChain, **relax_inputs)
print(f"Submitted relaxation with PK: {relax_wc.pk}")
```

## Advanced Workflows

### Band Structure Calculation

```python
from aiida_quantumespresso.workflows.pw.bands import PwBandsWorkChain

# Define high-symmetry k-points path
kpoints_path = orm.KpointsData()
kpoints_path.set_cell(structure.cell)
kpoints_path.set_kpoints_path([
    ('GAMMA', [0.0, 0.0, 0.0]),
    ('X', [0.5, 0.0, 0.0]),
    ('M', [0.5, 0.5, 0.0]),
    ('GAMMA', [0.0, 0.0, 0.0]),
    ('R', [0.5, 0.5, 0.5]),
], num_kpoints=20)

# Band structure inputs
bands_inputs = {
    'structure': structure,
    'pseudos': pseudos,
    'scf': {
        'pw': {
            'code': orm.load_code('pw@localhost'),
            'parameters': orm.Dict(dict=parameters),
            'kpoints': kpoints,
            'metadata': {
                'options': {
                    'max_wallclock_seconds': 1800,
                    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 4},
                }
            }
        }
    },
    'bands': {
        'pw': {
            'code': orm.load_code('pw@localhost'),
            'kpoints': kpoints_path,
            'metadata': {
                'options': {
                    'max_wallclock_seconds': 1800,
                    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 4},
                }
            }
        }
    }
}

# Submit band structure calculation
bands_wc = submit(PwBandsWorkChain, **bands_inputs)
print(f"Submitted band structure calculation with PK: {bands_wc.pk}")
```

### Custom Workflow with aiida-atomistic

```python
from aiida.engine import WorkChain, ToContext, calcfunction

@calcfunction
def analyze_magnetic_structure(structure):
    """Analyze magnetic properties of a structure."""
    from aiida import orm
    import numpy as np

    magnetic_sites = 0
    total_moment = np.array([0.0, 0.0, 0.0])

    for site in structure.sites:
        if hasattr(site, 'moment') and np.linalg.norm(site.moment) > 0:
            magnetic_sites += 1
            total_moment += site.moment

    results = {
        'magnetic_sites': magnetic_sites,
        'total_moment': total_moment.tolist(),
        'total_magnitude': float(np.linalg.norm(total_moment)),
    }

    return orm.Dict(dict=results)

class MagneticCalculationWorkChain(WorkChain):
    """Custom workchain for magnetic calculations."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('structure', valid_type=StructureData)
        spec.input('code', valid_type=orm.Code)
        spec.input('pseudos', valid_type=orm.UpfData, dynamic=True)
        spec.output('results', valid_type=orm.Dict)
        spec.outline(
            cls.analyze_structure,
            cls.run_calculation,
            cls.finalize,
        )

    def analyze_structure(self):
        """Analyze the input structure."""
        analysis = analyze_magnetic_structure(self.inputs.structure)
        self.ctx.analysis = analysis
        self.report(f"Structure analysis: {analysis.get_dict()}")

    def run_calculation(self):
        """Run the magnetic calculation."""
        # Here you would set up and run the actual calculation
        # based on the magnetic analysis
        pass

    def finalize(self):
        """Finalize the workflow."""
        self.out('results', self.ctx.analysis)

# Example usage
# magnetic_wc = submit(MagneticCalculationWorkChain,
#                     structure=magnetic_structure,
#                     code=orm.load_code('pw@localhost'),
#                     **pseudos)
```

## Monitoring and Analysis

### Checking Calculation Status

```python
# Check calculation status
def check_calculation(pk):
    """Check the status of a calculation."""
    node = orm.load_node(pk)

    print(f"Calculation {pk}:")
    print(f"  State: {node.process_state}")
    print(f"  Label: {node.label}")
    print(f"  Description: {node.description}")

    if node.is_finished_ok:
        print("  ✅ Finished successfully")
        if hasattr(node, 'outputs'):
            print(f"  Outputs: {list(node.outputs)}")
    elif node.is_failed:
        print("  ❌ Failed")
        if hasattr(node, 'exit_message'):
            print(f"  Error: {node.exit_message}")
    else:
        print(f"  ⏳ Running...")

# check_calculation(calculation.pk)
```

### Extracting Results

```python
def extract_results(calc_pk):
    """Extract results from a completed calculation."""
    calc = orm.load_node(calc_pk)

    if not calc.is_finished_ok:
        print("Calculation not finished successfully")
        return None

    results = {}

    if 'output_parameters' in calc.outputs:
        params = calc.outputs.output_parameters.get_dict()
        results['energy'] = params.get('energy')
        results['energy_units'] = params.get('energy_units', 'eV')

        if 'magnetization' in params:
            results['magnetization'] = params['magnetization']

    if 'output_structure' in calc.outputs:
        results['final_structure'] = calc.outputs.output_structure

    return results

# results = extract_results(calculation.pk)
# if results:
#     print(f"Final energy: {results['energy']} {results['energy_units']}")
```

## Best Practices

### Structure Preparation

```python
def prepare_structure_for_calculation(atoms, detect_kinds=True):
    """Prepare ASE atoms for AiiDA calculation."""

    # Convert to aiida-atomistic
    structure = StructureData.from_ase(atoms, detect_kinds=detect_kinds)

    # Validate structure
    if len(structure.sites) == 0:
        raise ValueError("Empty structure")

    # Check for reasonable cell volume
    volume = structure.properties.cell_volume
    if volume < 1.0:
        print("Warning: Very small cell volume")

    # Report structure info
    print(f"Structure prepared:")
    print(f"  Formula: {structure.properties.formula}")
    print(f"  Sites: {len(structure.sites)}")
    print(f"  Kinds: {len(structure.properties.kinds) if structure.properties.kinds else 'None'}")
    print(f"  Volume: {volume:.2f} Ų")

    return structure
```

### Error Handling

```python
def robust_submit(calc_class, inputs, max_retries=3):
    """Submit calculation with error handling."""

    for attempt in range(max_retries):
        try:
            calc = submit(calc_class, **inputs)
            print(f"Successfully submitted on attempt {attempt + 1}")
            return calc
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise

    return None
```

## Summary

✅ **Basic Calculations**: SCF calculations with aiida-atomistic structures
✅ **Magnetic Systems**: Collinear and non-collinear magnetism support
✅ **WorkChains**: Robust workflows with error handling
✅ **Advanced Workflows**: Band structures, relaxations, custom workflows
✅ **Monitoring Tools**: Status checking and result extraction
✅ **Best Practices**: Structure validation and error handling

## Next Steps

You now have the tools to run sophisticated calculations with aiida-atomistic! Explore the [API documentation](../reference/index.md) for more advanced features.
