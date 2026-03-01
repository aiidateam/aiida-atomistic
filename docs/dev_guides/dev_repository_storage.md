# Repository storage internals

This guide explains how `StructureData` stores and loads array properties, what
optimisations are already available to developers, and what the current format
limitations are together with suggested future improvements.

---

## Storage layout

When a `StructureData` node is stored, its data is split across two backends:

| Data | Backend | Queryable via `QueryBuilder`? |
| --- | --- | --- |
| Scalars and summary statistics (`cell`, `formula`, `n_sites`, …) | **Database attributes** | ✅ Yes |
| Array properties (`positions`, `charges`, `symbols`, …) | **AiiDA repository** (`.npz` file) | ❌ No |

The single repository file is called `properties.npz` (controlled by
`StructureData._properties_filename`).  It is a standard ZIP archive where
every property is stored as an independent `.npy` entry — one entry per
property name.

---

## The `.npz` format in detail

A `.npz` file created by `numpy.savez_compressed` is a **ZIP archive** with
`zipfile.ZIP_DEFLATED` (DEFLATE) compression.  Each member of the archive is
an independent `.npy` binary file containing exactly **one** numpy array.

```text
properties.npz  (ZIP archive)
├── charges.npy
├── positions.npy
├── site_indices_flat.npy      ← CSR part 1
├── site_indices_offsets.npy   ← CSR part 2
└── symbols.npy
```

Keys are stored in **sorted alphabetical order** to ensure a deterministic
binary output, which is required for AiiDA's content-addressable file hashing.

### Special case: `site_indices` (CSR encoding)

`site_indices` is a ragged list-of-lists (one sub-list per kind, with a
variable number of site indices).  A homogeneous numpy array cannot represent
it directly.  It is therefore encoded using
[CSR (Compressed Sparse Row)](https://en.wikipedia.org/wiki/Sparse_matrix#Compressed_sparse_row_(CSR,_CRS_or_Yale_format))
format as two flat 1-D `int64` arrays:

| Key in `.npz` | Shape | Content |
| --- | --- | --- |
| `site_indices_flat` | `(total_sites,)` | All indices concatenated |
| `site_indices_offsets` | `(n_kinds + 1,)` | Cumulative start positions |

**Example** — 3 kinds with 2, 1, and 3 sites respectively:

```text
site_indices = [[0, 1], [2], [3, 4, 5]]

→ site_indices_flat    = [0, 1, 2, 3, 4, 5]
→ site_indices_offsets = [0, 2, 3, 6]
```

Decoding: `site_indices[i] = flat[offsets[i] : offsets[i+1]]`

---

## Selective (per-property) loading

`_load_properties_from_npz` accepts an optional `keys` parameter that limits
which properties are decompressed:

```python
# Load only positions — charges, symbols, … are never touched
positions = node._load_properties_from_npz(keys=['positions'])['positions']

# Load two properties at once
data = node._load_properties_from_npz(keys=['positions', 'symbols'])

# site_indices — the CSR pair is expanded automatically
data = node._load_properties_from_npz(keys=['site_indices'])
```

**Why this is efficient:** `numpy.NpzFile.__getitem__` calls
`zipfile.ZipFile.open(key)` which seeks directly to the requested entry using
the ZIP central directory.  It does **not** decompress any other entry.
Accessing `positions` in a file that also contains `charges`, `magmoms`, and
`symbols` only decompresses `positions.npy`.

!!! note
    The full load (no `keys` argument) is cached on the node object after the
    first call, so repeated access to `.properties` does not re-read the file.


---

## Known limitation — no sliced or partial row access

It is **not** currently possible to read a subset of rows from a property
array (e.g. the positions of only the first 100 atoms out of 1 000 000).

**Root cause:** DEFLATE is a streaming compression codec.  To decompress byte
offset *N* inside a compressed stream, every byte from offset 0 to *N* must
be processed first.  There is no random-access point in the middle of a
compressed ZIP entry.

`numpy.load(..., mmap_mode='r')` does **not** help here — `mmap_mode` is
silently ignored for `.npz` files.  From the numpy source (`npyio.py`):

```python
if magic.startswith(_ZIP_PREFIX) or magic.startswith(_ZIP_SUFFIX):
    # zip-file (assume .npz)
    ret = NpzFile(fid, ...)
    return ret          # mmap_mode is never consulted
elif magic == format.MAGIC_PREFIX:
    # .npy file
    if mmap_mode:       # only reached for bare .npy files
        return format.open_memmap(file, mode=mmap_mode, ...)
```

`mmap_mode` only works when loading a **bare `.npy` file from disk** (not from
a stream and not from inside a ZIP).

---

## Future improvements

Two approaches would enable true random / sliced access:

### Option A — One `.npy` object per property

Store each array as a separate AiiDA repository object, e.g.:

```python
node.base.repository.put_object_from_filelike(buf, 'positions.npy')
node.base.repository.put_object_from_filelike(buf, 'charges.npy')
# … one call per property
```

A `.npy` file holds exactly **one** array, so N properties → N repository
objects (instead of the current single `properties.npz`).

**Advantages:**

- Files stored directly on disk support `np.load(..., mmap_mode='r')`, which
  memory-maps the array and allows zero-copy slicing of any row range without
  loading the full file into RAM.

**Disadvantages:**

- No compression → larger on-disk footprint.
- N repository objects instead of 1 → more file-system entries and more AiiDA
  metadata overhead.

### Option B — Zarr or HDF5 (recommended for large structures)

Replace `properties.npz` with a **Zarr** store or an **HDF5** file (via
`h5py`).  Both formats:

- Pack **multiple arrays into one file**.
- Use **chunked storage** with selectable compression (gzip, Blosc, …).
- Support **direct chunk-level random access** — reading row range
  `[i:j]` only decompresses the chunks that overlap that range.

This gives the best of both worlds: a single repository object, compression,
and efficient partial reads.

| Format | Single file | Compressed | Sliced access |
| --- | --- | --- | --- |
| Current `.npz` | ✅ | ✅ DEFLATE | ❌ streaming only |
| Per-property `.npy` | ❌ (N files) | ❌ | ✅ via `mmap_mode` |
| Zarr / HDF5 | ✅ | ✅ chunked | ✅ chunk-level |

---
