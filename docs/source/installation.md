# Installation

## Prerequisites

Before installing aiida-atomistic, ensure you have:

- Python 3.8 or later
- AiiDA core installed and configured
- A working AiiDA profile

If you don't have AiiDA set up yet, follow the [AiiDA installation guide](https://aiida.readthedocs.io/projects/aiida-core/en/latest/intro/get_started.html).

## Install aiida-atomistic

### From PyPI (Recommended)

```bash
pip install aiida-atomistic
```

### From Source (Development)

```bash
git clone https://github.com/aiidateam/aiida-atomistic.git
cd aiida-atomistic
pip install -e .
```

## Verify Installation

Test that everything is working correctly:

```python
from aiida import load_profile
load_profile()

from aiida_atomistic.data.structure import StructureData
print("✅ aiida-atomistic installed successfully!")
```

## Next Steps

Now that aiida-atomistic is installed, let's learn the [basic usage](basic_usage.md) patterns.
