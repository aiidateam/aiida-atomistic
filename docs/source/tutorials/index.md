# Tutorials

Welcome to the aiida-atomistic tutorials guide! These step-by-step tutorials will get you up and running with atomistic structures and calculations in AiiDA.

```{toctree}
:maxdepth: 2

1_first_structure
2_first_qe_calculation
```

## Learning Path

Our tutorials are designed to take you from beginner to advanced user:

### 📚 **Tutorial 1: Creating Your First Structure**
**Duration**: ~15 minutes
**Level**: Beginner

Learn the fundamentals of creating and manipulating atomic structures:

- ✅ Import `StructureData` and `StructureBuilder` classes
- ✅ Convert from ASE structures
- ✅ Explore structural properties and site information
- ✅ Modify structures with the mutable interface
- ✅ Store and retrieve structures from the AiiDA database

**Start here**: [Creating Your First Structure](1_first_structure.md)

### ⚙️ **Tutorial 2: Running Your First QE Calculation**
**Duration**: ~25 minutes
**Level**: Intermediate

Use your structures in real computational workflows:

- ✅ Set up Quantum ESPRESSO calculations
- ✅ Use WorkChains for robust calculations
- ✅ Run band structure and relaxation calculations
- ✅ Extract and analyze results

**Continue with**: [Running Calculations](2_first_qe_calculation.md)

## Quick Reference

### 🔍 **Need Something Specific?**
- **Magnetic Structures**: [Magnetic materials guide](../how_to/magnetic_structures.md)
- **Understanding Kinds**: [Efficiency optimization](../how_to/kinds.md)
- **Database Queries**: [Finding structures](../how_to/query.md)

## Prerequisites

Before starting, make sure you have:

- **Python 3.8+** installed
- **AiiDA core** installed and configured (`pip install aiida-core`)
- **aiida-atomistic** installed (`pip install aiida-atomistic`)
- **Basic familiarity** with Python and AiiDA concepts
- **Optional**: aiida-quantumespresso for calculations (`pip install aiida-quantumespresso`)

## Getting Help

- 📖 **API Documentation**: [Complete reference](../reference/api/index.html)
- 🐛 **Issues**: [Report bugs on GitHub](https://github.com/mikibonacci/aiida-atomistic/issues)
- 💬 **Discussions**: [Ask questions on AiiDA Discourse](https://aiida.discourse.group/)

Ready to start? Begin with [Creating Your First Structure](1_first_structure.md)! 🚀
