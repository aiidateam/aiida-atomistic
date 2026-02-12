# How-To Guides

Step-by-step guides for common tasks and workflows with `aiida-atomistic`.

```{toctree}
:maxdepth: 1

creation_mutation
magnetic_structures
hubbard_properties
kinds
define_custom
query
dev_adding_properties
dev_plugin_migration
```

## Quick Navigation

### 🏗️ **Creating and Modifying Structures**
Learn the basics of structure creation and manipulation:
- **How-to Guide**: [Creation and Mutation](creation_mutation.md)
- **Topics**: Initialization, mutable vs immutable, conversion methods
- **Use cases**: Building structures, importing from files

### 🧲 **Magnetic Structures**
Learn how to add magnetic moments and work with magnetic materials:
- **How-to Guide**: [Working with Magnetic Structures](magnetic_structures.md)
- **Topics**: Collinear magnetism, non-collinear spins, magnetic kinds
- **Use cases**: Magnetic materials, spin-polarized calculations

## User Guides

### 🏗️ **Creating and Modifying Structures**
Learn the basics of structure creation and manipulation:
- **How-to Guide**: [Creation and Mutation](creation_mutation.md)
- **Topics**: Initialization methods, mutable vs immutable, conversion between formats
- **Use cases**: Building structures from scratch, importing from files, modifying existing structures

**What you'll learn:**
- Create structures from dictionaries, ASE, pymatgen
- Use `StructureDataMutable` for building and editing
- Convert between mutable and immutable structures
- Export to various formats (CIF, MCIF, ASE, pymatgen)

### 🧲 **Working with Magnetic Structures**
Add and manipulate magnetic properties:
- **How-to Guide**: [Magnetic Structures](magnetic_structures.md)
- **Topics**: Collinear and non-collinear magnetism, magnetic kinds, total magnetization
- **Use cases**: Magnetic materials, spin-polarized DFT calculations, magnetic ordering

**What you'll learn:**
- Set collinear magnetic moments
- Define non-collinear spin orientations
- Work with magnetic kinds
- Calculate total magnetization

### 🏷️ **Understanding and Using Kinds**
Master the kinds system for efficient structure representation:
- **How-to Guide**: [Working with Kinds](kinds.md)
- **Topics**: Automatic kind generation, tolerance system, kind validation, manual assignment
- **Applications**: Storage optimization, plugin compatibility, large structures

**What you'll learn:**
- What kinds are and why they matter
- Generate kinds automatically with `generate_kinds()`
- Control tolerances for property comparison
- Validate kind consistency
- Access kind-based structure representations

### 🎨 **Defining Custom Properties**
Store additional structure-related information:
- **How-to Guide**: [Custom Properties](define_custom.md)
- **Topics**: Using the `custom` dictionary, when to use extras instead
- **Use cases**: Plugin-specific data, experimental metadata, specialized properties

**What you'll learn:**
- Store custom data in structures
- Difference between `custom` dict and AiiDA extras
- Best practices for custom properties

### 🔍 **Querying Structures**
Find and analyze structures in your database:
- **How-to Guide**: [Querying Structures](query.md)
- **Topics**: Search patterns, property filtering, QueryBuilder usage
- **Tools**: AiiDA QueryBuilder integration

**What you'll learn:**
- Query structures by properties
- Filter by composition, magnetic properties, etc.
- Efficient database searches

## Developer Guides

### 🔧 **Adding New Properties**
Extend aiida-atomistic with new property types:
- **Developer Guide**: [Adding Properties](dev_adding_properties.md)
- **Topics**: Site vs global properties, computed fields, setters/getters, validation, testing
- **For**: Contributors adding features to aiida-atomistic

**What you'll learn:**
- Add new site properties with full integration
- Add new global properties
- Implement computed fields for array access
- Write validators and tests
- Contribute via fork and pull request

### 🔌 **Migrating Your Plugin**
Update your AiiDA plugin to support aiida-atomistic:
- **Developer Guide**: [Plugin Migration](dev_plugin_migration.md)
- **Topics**: Property validation, supported properties, backward compatibility
- **For**: Plugin developers migrating from legacy `orm.StructureData`

**What you'll learn:**
- Access properties via the `properties` attribute
- Validate supported properties in CalcJobs
- Handle unsupported properties gracefully
- Support both legacy and atomistic structures
- Real examples from aiida-quantumespresso

## Related Documentation

- **[In-Depth Guides](../in_depth/index.md)**: Deep dives into concepts
  - [Property Types](../in_depth/properties.md)
  - [Immutability](../in_depth/immutability.md)
  - [Code Architecture](../in_depth/structure_of_the_code.md)

- **[Tutorials](../tutorials/index.md)**: Complete workflow examples

- **[API Reference](../reference/api/index.md)**: Detailed API documentation


### 🔍 **Understanding Kinds**
Deep dive into the kinds system for efficiency:
- **How-to Guide**: [Working with Kinds](kinds.md)
- **Topics**: Automatic grouping, storage optimization, tolerances
- **Applications**: Large structures, repeated calculations

### 🗃️ **Querying Structures**
Find and analyze structures in your database:
- **How-to Guide**: [Querying Structures](query.md)
- **Topics**: Search patterns, property filtering, analysis workflows
- **Tools**: AiiDA QueryBuilder integration
