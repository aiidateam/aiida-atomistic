# In-Depth Guides

Comprehensive explanations of core concepts and advanced topics in `aiida-atomistic`.

```{toctree}
:maxdepth: 2

properties
immutability
storage_backends
structure_of_the_code
```

## Core Concepts

### 🏗️ **Property Types and Architecture**

Understanding the property system in aiida-atomistic:
- **Guide**: [Property Types](properties.md)
- **Topics**: Global vs site vs computed properties, property formats, naming conventions
- **Why it matters**: Understanding how to access and use structure properties effectively

**Key takeaways:**
- Individual site properties (singular: `charge`, `magmom`) vs computed arrays (plural: `charges`, `magmoms`)
- Global properties apply to entire structure (`pbc`, `cell`, `hubbard`)
- Computed properties are derived on-the-fly (`formula`, `kinds`, `dimensionality`)
- Statistical properties for efficient queries (`max_charge`, `min_magmom`, etc.)
- Clear property access patterns and formats

### 🔒 **Immutability**

Understanding the immutability model and its implications:
- **Guide**: [Immutability in StructureData](immutability.md)
- **Topics**: Immutable vs mutable structures, frozen data types, best practices
- **Why it matters**: Data provenance, workflow reproducibility, AiiDA integration

**Key takeaways:**
- `StructureData` is immutable for provenance tracking
- `StructureDataMutable` for construction and modification
- How to work with frozen lists and sites
- Converting between mutable and immutable structures

### 💾 **Storage Backends**

Understanding data storage strategies:
- **Guide**: [Storage Backends](storage_backends.md)
- **Topics**: Attribute-based vs repository-based storage, metadata-driven decisions, querying
- **Why it matters**: Choosing the right backend for performance and scalability

**Key takeaways:**
- `StructureData`: All data in database attributes (queryable, simple)
- `StructureDataRepository`: Arrays in `.npz` files, metadata in database (scalable)
- Metadata controls storage location (`store_in="db"` vs `store_in="npz"`)
- Trade-offs between queryability and storage efficiency

### ⚙️ **Code Architecture**

Internal structure and organization of the codebase:
- **Guide**: [Structure of the Code](structure_of_the_code.md)
- **Topics**: Module organization, class hierarchy, design patterns
- **For**: Developers extending or contributing to aiida-atomistic

## Advanced Topics

### Property System Details

How properties are implemented:
- **Site properties**: Stored in `Site` model, accessed via `sites[i].property`
- **Computed arrays**: Aggregated from sites using `@computed_field` decorators
- **Global properties**: Stored in `StructureBaseModel`, apply to whole structure
- **Validation**: Pydantic field validators and model validators

### Performance Optimizations

Structure operations and storage efficiency:
- **Kind-based storage**: Compress repeated atoms for database efficiency
- **Computed field caching**: Automatic memoization of expensive calculations
- **Efficient copying**: Specialized methods for deep/shallow copies
- **Lazy evaluation**: Properties computed only when accessed

### Validation System

Ensuring data integrity:
- **Field-level validation**: Pydantic validators for each property
- **Cross-property validation**: Model validators for consistency checks
- **Kind validation**: Ensuring sites with same kind have same properties
- **Site proximity checks**: Detecting atoms too close together
- **Tolerance system**: Configurable precision for property comparisons

## Related Documentation

- **[How-to Guides](../how_to/index.md)**: Step-by-step instructions for common tasks
  - [Creating Structures](../how_to/creation_mutation.md)
  - [Working with Kinds](../how_to/kinds.md)
  - [Magnetic Structures](../how_to/magnetic_structures.md)
  - [Adding Properties](../how_to/dev_adding_properties.md)
  - [Plugin Migration](../how_to/dev_plugin_migration.md)

- **[Tutorials](../tutorials/index.md)**: Learn by example with complete workflows

- **[Reference](../reference/api/index.md)**: Detailed API documentation
