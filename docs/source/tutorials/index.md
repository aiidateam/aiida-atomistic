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
**Duration**: ~5 minutes
**Level**: Beginner

Learn the fundamentals of creating and manipulating atomic structures:

- Import `StructureData` and `StructureBuilder` classes
- Convert from ASE structures
- Explore structural properties and site information
- Modify structures with the mutable interface
- Store and retrieve structures from the AiiDA database

**Start here**: [Creating Your First Structure](1_first_structure.md)

### ⚙️ **Tutorial 2: Running Your First QE Calculation**
**Duration**: ~10 minutes
**Level**: Intermediate

Use your structures in real computational workflows:

- Set up Quantum ESPRESSO calculations
- Use `PwBaseWorkChain` to submit self-consistent field (SCF) calculation
- Add total charge to the system and run again

**Continue with**: [Running Calculations](2_first_qe_calculation.md)

Ready to start? Begin with [Creating Your First Structure](1_first_structure.md)! 🚀
