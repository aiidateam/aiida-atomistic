# Magnetic Structures

## Introduction

AiiDA-atomistic provides comprehensive support for magnetic properties in crystal structures. This enables modeling of magnetic materials with proper magnetic moment assignments and collinear/non-collinear magnetism support.

## Basic Magnetic Properties

### Adding Magnetic Moments

```python
import numpy as np
from aiida_atomistic.data.structure import StructureDataMutable

# Start with a basic iron structure
from ase.build import bulk
fe_atoms = bulk('Fe', 'bcc', a=2.87)

# Create mutable structure
structure = StructureDataMutable.from_ase(fe_atoms)

# Add magnetic moments
for site in structure.sites:
    site.moment = np.array([0.0, 0.0, 2.2])  # 2.2 µB along z-axis

print(f"Added magnetic moments to {len(structure.sites)} sites")
```

### Collinear Magnetism

For simple collinear magnetic structures:

```python
# Create antiferromagnetic NiO structure
from ase.build import rocksalt
nio_atoms = rocksalt(['Ni', 'O'], a=4.18, factor=2)

structure = StructureDataMutable.from_ase(nio_atoms)

# Assign magnetic moments
for i, site in enumerate(structure.sites):
    if site.symbol == 'Ni':
        # Alternate spin directions for antiferromagnetism
        moment_value = 1.64 if i % 2 == 0 else -1.64
        site.moment = np.array([0.0, 0.0, moment_value])
    else:
        site.moment = np.array([0.0, 0.0, 0.0])  # Oxygen is non-magnetic

print(f"Created antiferromagnetic NiO structure")
print(f"Magnetic sites: {sum(1 for s in structure.sites if np.linalg.norm(s.moment) > 0)}")
```

### Non-Collinear Magnetism

For complex magnetic structures with arbitrary moment directions:

```python
# Create a frustrated magnetic system
from ase.build import bulk
mn_atoms = bulk('Mn', 'fcc', a=3.89, cubic=True)
mn_atoms *= (2, 2, 1)  # 2x2x1 supercell

structure = StructureDataMutable.from_ase(mn_atoms)

# Define non-collinear magnetic moments (120° configuration)
import math
angle = 2 * math.pi / 3  # 120 degrees

for i, site in enumerate(structure.sites):
    theta = i * angle
    moment_magnitude = 2.0
    site.moment = np.array([
        moment_magnitude * math.cos(theta),
        moment_magnitude * math.sin(theta),
        0.0
    ])

print(f"Created non-collinear magnetic structure")
print(f"Example moment directions:")
for i, site in enumerate(structure.sites[:3]):
    print(f"  Site {i}: {site.moment}")
```

## Working with Magnetic Kinds

The kinds system intelligently groups atoms with identical magnetic properties:

```python
# Create structure with magnetic kinds
structure = StructureDataMutable.from_ase(nio_atoms, detect_kinds=True)

# Add magnetic moments
for site in structure.sites:
    if site.symbol == 'Ni':
        # All Ni atoms get the same moment initially
        site.moment = np.array([0.0, 0.0, 1.64])

# Convert to immutable to trigger kinds detection
final_structure = StructureData.from_mutable(structure)

print(f"Magnetic kinds detected:")
for kind in final_structure.properties.kinds:
    if hasattr(kind, 'moment') and np.linalg.norm(kind.moment) > 0:
        print(f"  {kind.kind_name}: {kind.symbol} with moment {kind.moment}")
```

### Different Magnetic Environments

```python
# Create complex magnetic structure with different environments
structure = StructureDataMutable()

# Define unit cell
structure.cell = np.array([
    [5.0, 0.0, 0.0],
    [0.0, 5.0, 0.0],
    [0.0, 0.0, 10.0]
])
structure.pbc = [True, True, True]

# Add sites with different magnetic moments
sites_data = [
    {"symbol": "Fe", "position": [0.0, 0.0, 0.0], "moment": [0.0, 0.0, 2.3]},
    {"symbol": "Fe", "position": [2.5, 2.5, 0.0], "moment": [0.0, 0.0, -2.3]},
    {"symbol": "Fe", "position": [0.0, 2.5, 5.0], "moment": [2.0, 0.0, 0.0]},
    {"symbol": "Fe", "position": [2.5, 0.0, 5.0], "moment": [-2.0, 0.0, 0.0]},
]

for site_data in sites_data:
    structure.append_atom(
        symbol=site_data["symbol"],
        position=site_data["position"],
        moment=site_data["moment"]
    )

# Convert and check kinds
final_structure = StructureData.from_mutable(structure)
print(f"Created {len(final_structure.properties.kinds)} magnetic kinds")
```

## Magnetic Property Analysis

### Computing Magnetic Properties

```python
# Analyze magnetic structure
def analyze_magnetism(structure):
    """Analyze magnetic properties of a structure."""
    magnetic_sites = [s for s in structure.sites
                     if hasattr(s, 'moment') and np.linalg.norm(s.moment) > 0]

    if not magnetic_sites:
        print("No magnetic sites found")
        return

    # Total magnetic moment
    total_moment = sum(s.moment for s in magnetic_sites)
    total_magnitude = np.linalg.norm(total_moment)

    print(f"Magnetic analysis:")
    print(f"  Magnetic sites: {len(magnetic_sites)}/{len(structure.sites)}")
    print(f"  Total moment: {total_moment}")
    print(f"  Total magnitude: {total_magnitude:.3f} µB")

    # Average moment magnitude
    moments = [np.linalg.norm(s.moment) for s in magnetic_sites]
    avg_moment = np.mean(moments)
    print(f"  Average moment magnitude: {avg_moment:.3f} µB")

    return {
        'total_moment': total_moment,
        'magnetic_sites': len(magnetic_sites),
        'average_magnitude': avg_moment
    }

# Analyze our structures
analyze_magnetism(final_structure)
```

### Magnetic Moment Directions

```python
def magnetic_analysis_detailed(structure):
    """Detailed magnetic moment analysis."""
    magnetic_sites = [s for s in structure.sites
                     if hasattr(s, 'moment') and np.linalg.norm(s.moment) > 0]

    print("Detailed magnetic moment analysis:")

    # Group by moment direction (collinear check)
    moment_directions = {}
    for site in magnetic_sites:
        moment = site.moment
        direction = moment / np.linalg.norm(moment)

        # Round to avoid floating point issues
        direction_key = tuple(np.round(direction, 3))

        if direction_key not in moment_directions:
            moment_directions[direction_key] = []
        moment_directions[direction_key].append(site)

    print(f"  Found {len(moment_directions)} unique moment directions:")
    for direction, sites in moment_directions.items():
        print(f"    Direction {direction}: {len(sites)} sites")
        moments = [np.linalg.norm(s.moment) for s in sites]
        print(f"      Moment magnitudes: {moments}")

magnetic_analysis_detailed(final_structure)
```

## Advanced Magnetic Features

### Spin-Orbit Coupling Effects

```python
# Structure with spin-orbit coupling considerations
structure = StructureDataMutable()

# Add sites with complex magnetic anisotropy
sites_with_anisotropy = [
    {
        "symbol": "Co",
        "position": [0.0, 0.0, 0.0],
        "moment": [0.1, 0.0, 1.6],  # Small xy component due to SOC
        "kind_name": "Co_anisotropic"
    }
]

for site_data in sites_with_anisotropy:
    structure.append_atom(**site_data)

print("Added sites with magnetic anisotropy effects")
```

### Magnetic File I/O

```python
# Save magnetic structure
magnetic_structure = StructureData.from_mutable(structure)
magnetic_structure.store()

# The magnetic information is preserved in the database
loaded = orm.load_node(magnetic_structure.pk)

print("Magnetic information preserved:")
for site in loaded.sites:
    if hasattr(site, 'moment') and np.linalg.norm(site.moment) > 0:
        print(f"  {site.symbol}: {site.moment}")
```

## Integration with Calculations

### Preparing for Quantum ESPRESSO

```python
# Structure optimized for QE calculations
def prepare_for_qe(structure, magnetic_setup='collinear'):
    """Prepare magnetic structure for Quantum ESPRESSO."""

    # Get starting magnetization for each kind
    starting_magnetization = {}

    for kind in structure.properties.kinds:
        if hasattr(kind, 'moment') and np.linalg.norm(kind.moment) > 0:
            if magnetic_setup == 'collinear':
                # Use z-component for collinear
                mag_value = kind.moment[2]
            else:
                # Use magnitude for non-collinear
                mag_value = np.linalg.norm(kind.moment)

            starting_magnetization[kind.kind_name] = mag_value

    print(f"QE starting magnetization:")
    for kind, mag in starting_magnetization.items():
        print(f"  {kind}: {mag:.3f}")

    return starting_magnetization

# Example usage
qe_mag_params = prepare_for_qe(final_structure, 'collinear')
```

## Summary

✅ **Collinear & Non-collinear**: Support for both simple and complex magnetism
✅ **Kinds Integration**: Automatic grouping of magnetically equivalent sites
✅ **Property Analysis**: Tools for analyzing magnetic configurations
✅ **Database Storage**: Magnetic information preserved in AiiDA database
✅ **Calculation Ready**: Easy integration with DFT codes

## Next Steps

Learn how to run [calculations](calculations.md) with your magnetic structures!
