from __future__ import annotations
import tempfile
import numpy as np
import warnings

from typing import Optional

from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.models import (
    MutableStructureModel,
    ImmutableStructureModel,
)
from aiida_atomistic.data.structure.setter_mixin import SetterMixin
from aiida_atomistic.data.structure.getter_mixin import GetterMixin


def _resolve_site_indices(sites, index):
    """
    Validate *index* against *sites* and return the selected sub-list.

    This is the single shared implementation used by both
    :meth:`StructureData.__getitem__` and :meth:`StructureBuilder.__getitem__`
    so that index handling and error messages are identical in both classes.

    :param sites: The full list of site objects (``Site`` or ``FrozenSite``).
    :param index: An ``int``, ``slice``, ``list``/``tuple`` of ints, or a
        1-D integer numpy array.
    :return: A list of the selected site objects.
    :raises IndexError: If any integer index is out of range.
    :raises TypeError: If *index* is not a supported type, or if a
        list/array contains non-integer elements.
    """
    n = len(sites)

    if isinstance(index, (int, np.integer)):
        if index < -n or index >= n:
            raise IndexError(
                f"Site index {index} out of range for structure with {n} sites."
            )
        return [sites[int(index)]]

    if isinstance(index, slice):
        return list(sites[index])

    if isinstance(index, (list, tuple, np.ndarray)):
        result = []
        for raw in index:
            if not isinstance(raw, (int, np.integer)):
                raise TypeError(
                    f"All elements of an index list must be integers, got {type(raw)}."
                )
            i = int(raw)
            if i < -n or i >= n:
                raise IndexError(
                    f"Site index {i} out of range for structure with {n} sites."
                )
            result.append(sites[i])
        return result

    raise TypeError(
        f"Unsupported index type {type(index)}. "
        "Use int, slice, or a list/array of ints."
    )


class StructureData(Data, GetterMixin):
    """
    A StructureData class that stores properties in the repository instead of attributes.

    This class stores selected properties in a single compressed .npz file in the repository.
    Only properties useful for querying are stored in database attributes.

    This approach is more efficient for large structures as it avoids storing
    large arrays in the database.
    """

    _mutable = False
    _model = ImmutableStructureModel

    # Filename for the properties npz file
    _properties_filename = "properties.npz"

    # Whether to store array shape metadata in attributes for querying
    _store_shape_metadata = False

    # Field metadata key that can be set on model fields to drive storage
    _storage_metadata_key = "store_in"

    # Supported metadata values
    _storage_repository_values = {"npz", "repo", "repository"}
    _storage_attribute_values = {"db", "attribute", "attributes"}

    def __init__(self, sites: list[dict] = None, kinds: list[dict] = None, **kwargs):
        """
        Initialize a StructureData instance.

        :param sites: list of site dictionaries
        :param kinds: list of kind dictionaries
        :param kwargs: Additional properties (pbc, cell, etc.)
        """
        from aiida_atomistic.data.structure.utils_kinds import sites_from_kinds

        # if both sites and kinds are provided, we use kinds and we print a warning
        # basically, we map kinds->sites, as the structure object is site-based
        if sites is not None and kinds is not None:
            warnings.warn(
                "Provided both `sites` and `kinds` information. "
                "Dropping the `sites` information and using only `kinds`."
            )
            sites = sites_from_kinds(kinds)
        elif kinds is not None:
            sites = sites_from_kinds(kinds)

        # Here we populate the properties attribute
        self._properties = self._model(sites=sites, **kwargs)
        super().__init__()

        # Cache for the reconstructed model
        self._cached_npz_properties = None
        self._cached_model_instance: Optional[object] = None

        # Store the properties
        self._store_properties()

    @staticmethod
    def _is_numeric_array(value) -> bool:
        """Return True if the value is a numeric numpy array (or convertible)."""
        if isinstance(value, np.ndarray):
            return value.dtype.kind in {"i", "f", "u", "c"}
        if isinstance(value, list):
            try:
                arr = np.asarray(value)
            except (ValueError, TypeError):
                return False
            return arr.dtype.kind in {"i", "f", "u", "c"}
        return False

    @staticmethod
    def _is_string_array(value) -> bool:
        """Return True if the value is a string array (list of strings or numpy unicode array)."""
        if isinstance(value, np.ndarray):
            return value.dtype.kind in {"U", "S"}
        if isinstance(value, list) and value and all(isinstance(v, str) for v in value):
            return True
        return False

    @classmethod
    def get_queryable_properties(cls, include_internal: bool = False) -> dict:
        """
        Get all properties that can be queried via QueryBuilder.

        For repository-based storage, ONLY properties stored in database attributes
        are queryable. Properties stored in .npz files CANNOT be queried directly.

        :param include_internal: If True, include internal properties like 'sites'.
                                 Default is False.
        :return: Dictionary with property classifications:
                 - 'queryable': Properties stored in database (can be queried)
                 - 'not_queryable': Properties stored in .npz or not stored (cannot be queried)

        Example:
            >>> props = StructureData.get_queryable_properties()
            >>> print(props['queryable'])
            ['cell', 'cell_volume', 'custom', 'dimensionality', 'formula',
             'has_vacancies', 'is_alloy', 'kind_names', 'max_charge',
             'min_charge', 'n_sites', 'pbc', 'symbols', 'tot_charge', ...]
            >>> print(props['not_queryable'])
            ['charges', 'kinds', 'magmoms', 'magnetizations', 'masses',
             'positions', 'weights']
        """
        queryable = set()
        not_queryable = set()

        # Process regular fields
        for field_name, field_info in cls._model.model_fields.items():
            if field_name in ("sites", "kinds") and not include_internal:
                not_queryable.add(field_name)
                continue

            metadata = field_info.json_schema_extra or {}
            store_in = metadata.get(cls._storage_metadata_key, "").lower()

            # Determine storage target from metadata
            if store_in in cls._storage_repository_values:
                target = "repository"
            elif store_in in cls._storage_attribute_values:
                target = "attributes"
            else:
                # Default: attributes for regular fields
                target = "attributes"

            # Only attributes are queryable!
            if target == "attributes":
                queryable.add(field_name)
            else:
                not_queryable.add(field_name)

        # Process computed fields
        for field_name, field_info in cls._model.model_computed_fields.items():
            if field_name in ("sites", "kinds") and not include_internal:
                not_queryable.add(field_name)
                continue

            metadata = getattr(field_info, "json_schema_extra", None) or {}
            store_in = metadata.get(cls._storage_metadata_key, "").lower()

            # Computed fields without explicit store_in are not stored (so not queryable)
            if cls._storage_metadata_key not in metadata:
                not_queryable.add(field_name)
                continue

            # Only attributes are queryable!
            if store_in in cls._storage_attribute_values:
                queryable.add(field_name)
            else:
                not_queryable.add(field_name)

        return {
            "queryable": sorted(queryable),
            "not_queryable": sorted(not_queryable),
        }

    @classmethod
    def print_queryable_properties(cls):
        """
        Print a formatted overview of which properties can be queried.

        This is useful for understanding what properties are available for
        filtering in QueryBuilder when using repository-based storage.

        IMPORTANT: Only properties stored in database attributes can be queried.
        Properties stored in .npz files are not queryable via QueryBuilder.

        Example:
            >>> StructureData.print_queryable_properties()

            ═══════════════════════════════════════════════════════════════
            Queryable Properties for StructureData
            ═══════════════════════════════════════════════════════════════

            ✓ QUERYABLE (stored in database attributes):
              • cell
              • cell_volume
              • custom
              • dimensionality
              • formula
              • has_vacancies
              • is_alloy
              • kind_names
              • max_charge
              • max_magmom
              • max_magnetization
              • min_charge
              • min_magmom
              • min_magnetization
              • n_sites
              • pbc
              • symbols
              • tot_charge
              • tot_magnetization

            ✗ NOT QUERYABLE (stored in .npz repository):
              • charges
              • magmoms
              • magnetizations
              • masses
              • positions
              • weights

            ⚠ NOT QUERYABLE (computed on-the-fly, not stored):
              • kinds

            Note: Use QueryBuilder filters only on queryable properties.
                  Example: qb.append(StructureData,
                                    filters={'attributes.formula': 'Si2',
                                            'attributes.max_charge': {'>': 0.5}})
        """
        props = cls.get_queryable_properties()

        print("\n" + "═" * 63)
        print(f"Queryable Properties for {cls.__name__}")
        print("═" * 63)

        if props["queryable"]:
            print("\n✓ QUERYABLE (stored in database attributes):")
            for prop in props["queryable"]:
                print(f"  • {prop}")

        if props["not_queryable"]:
            # Separate stored vs computed
            computed_not_stored = set()
            repository_stored = set()

            for prop in props["not_queryable"]:
                # Check if it's a computed field without store_in
                if prop in cls._model.model_computed_fields:
                    metadata = (
                        getattr(
                            cls._model.model_computed_fields[prop],
                            "json_schema_extra",
                            None,
                        )
                        or {}
                    )
                    if cls._storage_metadata_key not in metadata:
                        computed_not_stored.add(prop)
                        continue
                repository_stored.add(prop)

            if repository_stored:
                print("\n✗ NOT QUERYABLE (stored in .npz repository):")
                for prop in sorted(repository_stored):
                    print(f"  • {prop}")

            if computed_not_stored:
                print("\n⚠ NOT QUERYABLE (computed on-the-fly, not stored):")
                for prop in sorted(computed_not_stored):
                    print(f"  • {prop}")

        print("\nNote: Use QueryBuilder filters only on queryable properties.")
        print(f"      Example: qb.append({cls.__name__},")
        print("                         filters={'attributes.formula': 'Si2',")
        print(
            "                                 'attributes.max_charge': {'>': 0.5}})\n"
        )

    @classmethod
    def detect_storage_backend(cls, prop_name: str) -> str:
        """
        Detect the storage backend for a property based on its metadata.

        :param prop_name: Name of the property
        :return: Storage backend ('db', 'npz', 'repo', etc.)
        """
        if prop_name in cls._model.model_fields.keys():
            json_schema_extra = (
                cls._model.model_fields[prop_name].json_schema_extra or {}
            )
            store_in = json_schema_extra.get(cls._storage_metadata_key, "").lower()
        elif prop_name in cls._model.model_computed_fields.keys():
            computed_field_info = cls._model.model_computed_fields[prop_name]
            json_schema_extra = (
                getattr(computed_field_info, "json_schema_extra", None) or {}
            )
            store_in = json_schema_extra.get(cls._storage_metadata_key, "").lower()
        else:
            store_in = "db"  # default to db for unknown properties

        return store_in

    def _store_properties(self):
        """Store properties in the AiiDA db and/or in a single npz file in the repository."""

        attributes = self.properties.model_dump(
            exclude_unset=True, exclude_none=True, warnings=False
        )

        # Handle kind-based compression if needed
        if self.properties.kind_names is not None:
            from aiida_atomistic.data.structure.utils_kinds import (
                compress_properties_by_kind,
            )

            compressed = compress_properties_by_kind(attributes)
            attributes.update(compressed)

        # Remove and sites/kinds
        attributes.pop("sites", None)
        attributes.pop("kinds", None)

        # Separate numpy arrays from other properties
        repository_dict = {}
        database_dict = {}

        for prop_name, value in attributes.items():
            if value is None:
                continue

            target = self.detect_storage_backend(prop_name)

            if target == "repository" and self._is_numeric_array(value):
                arr = np.asarray(value)
                repository_dict[prop_name] = arr
                if self._store_shape_metadata:
                    database_dict[f"shape|{prop_name}"] = list(arr.shape)
            elif target == "repository" and self._is_string_array(value):
                arr = np.asarray(value, dtype=str)
                repository_dict[prop_name] = arr
                if self._store_shape_metadata:
                    database_dict[f"shape|{prop_name}"] = list(arr.shape)
            elif prop_name == "site_indices":
                # site_indices is a ragged list-of-lists (one per kind, variable length because of different number of sites per kind).
                # Encode as two flat 1D int arrays using CSR format so the npz stays
                # homogeneous (allow_pickle=False compatible):
                #   site_indices_flat    : all indices concatenated, shape (total_sites,)
                #   site_indices_offsets : cumulative start positions, shape (n_kinds + 1,)
                # e.g. [[0,1],[2],[3,4,5]] → flat=[0,1,2,3,4,5], offsets=[0,2,3,6]
                flat = np.array(
                    [idx for sublist in value for idx in sublist], dtype=np.int64
                )
                lengths = np.array([len(sublist) for sublist in value], dtype=np.int64)
                offsets = np.concatenate([[0], np.cumsum(lengths)]).astype(np.int64)
                repository_dict["site_indices_flat"] = flat
                repository_dict["site_indices_offsets"] = offsets
            else:
                database_dict[prop_name] = value

        # Save all arrays to a single compressed npz file
        if repository_dict:
            with tempfile.NamedTemporaryFile(suffix=".npz") as handle:
                # Sort keys to ensure deterministic binary output for hashing
                # savez_compressed will indeed respect the order of keys, for Python 3.7+ where dicts maintain insertion order, but we sort explicitly to be safe and clear
                np.savez_compressed(
                    handle,
                    **{k: repository_dict[k] for k in sorted(repository_dict.keys())},
                )
                handle.flush()
                handle.seek(0)

                # Store in repository
                self.base.repository.put_object_from_filelike(
                    handle, self._properties_filename
                )

        # Store attributes (query-friendly metadata and non-array properties)
        for key, value in database_dict.items():
            self.base.attributes.set(key, value)

    def _load_properties_from_npz(self, keys: list = None) -> dict:
        """
        Load properties from the npz file in the repository.

        **For developers — selective loading**

        The ``.npz`` container is a ZIP archive where every property is stored
        as an independent ``.npy`` entry.  ``NpzFile.__getitem__`` (numpy's
        internal accessor) uses ``zipfile.ZipFile.open(key)`` to seek directly
        to the requested entry in the central ZIP directory — it does **not**
        decompress any other entries.  This means that passing ``keys`` loads
        and decompresses *only* the requested properties, leaving the rest
        untouched.  For large structures with many heavy arrays this can give a
        significant speed and memory benefit.

        Usage example::

            # Load only positions (avoids decompressing charges, magmoms, …)
            positions = node._load_properties_from_npz(keys=['positions'])['positions']

            # Load two properties at once
            data = node._load_properties_from_npz(keys=['positions', 'symbols'])

            # site_indices is stored internally as two CSR arrays; the key
            # expansion is handled automatically:
            data = node._load_properties_from_npz(keys=['site_indices'])

        **Known limitation — no sliced / partial row access**

        Reading a slice of rows (e.g. ``positions[0:100]``) is **not**
        possible with the current ``.npz`` format.  The ZIP compression codec
        (DEFLATE) is a streaming algorithm: to reach byte offset *N* inside a
        compressed entry the entire stream from byte 0 must be decompressed
        first.  ``mmap_mode`` in ``numpy.load`` is also silently ignored for
        ``.npz`` files (it only applies to bare ``.npy`` files on disk).

        Future approaches that would enable true random / sliced access:

        * Store each property as a **separate ``.npy`` object** in the AiiDA
          repository.  A ``.npy`` file holds exactly **one** array, so this
          requires one ``put_object_from_filelike`` call per property (e.g.
          ``positions.npy``, ``charges.npy``, ``symbols.npy``, …) instead of
          the single ``properties.npz`` used today.  The trade-off is more
          repository objects and no compression, but ``.npy`` files on disk
          support ``np.load(..., mmap_mode='r')`` which memory-maps the array
          and allows zero-copy slicing without loading the full file.
        * Switch the container format to **Zarr** or **HDF5** (h5py), both of
          which pack multiple arrays into one file *and* store them in
          fixed-size compressed chunks, enabling direct chunk-level random
          access without touching the rest of the file.

        :param keys: Optional list of property names to load.  If ``None``
            (default) all properties stored in the file are loaded.  Unknown
            keys are silently ignored.
        :return: Dictionary of property name -> numpy array (or Python list
            for string properties).
        """
        if self._properties_filename not in self.base.repository.list_object_names():
            return {}

        with self.base.repository.open(self._properties_filename, mode="rb") as handle:
            npz_data = np.load(handle, allow_pickle=False)

            # Determine which internal npz keys to read.
            # site_indices is stored as two CSR arrays, so expand accordingly.
            if keys is None:
                keys_to_read = list(npz_data.files)
            else:
                # Always include CSR pair when site_indices is requested
                internal_keys = set()
                for k in keys:
                    if k == "site_indices":
                        internal_keys.update(
                            ["site_indices_flat", "site_indices_offsets"]
                        )
                    else:
                        internal_keys.add(k)
                keys_to_read = [k for k in npz_data.files if k in internal_keys]

            # Only the keys in keys_to_read are decompressed from the ZIP.
            # String arrays (dtype 'U' or 'S') are converted back to Python lists.
            properties = {}
            for key in keys_to_read:
                arr = npz_data[key]  # decompresses only this one ZIP entry
                if arr.dtype.kind in {"U", "S"}:
                    properties[key] = arr.tolist()
                else:
                    properties[key] = arr

            # Decode CSR-encoded site_indices back into list-of-lists
            if (
                "site_indices_flat" in properties
                and "site_indices_offsets" in properties
            ):
                flat = properties.pop("site_indices_flat")
                offsets = properties.pop("site_indices_offsets")
                properties["site_indices"] = [
                    flat[offsets[i] : offsets[i + 1]].tolist()
                    for i in range(len(offsets) - 1)
                ]

        # Cache the full load (only when all keys were requested)
        if keys is None and self.is_stored:
            self._cached_npz_properties = properties

        return properties

    @property
    def properties(self):
        """
        Reconstruct the properties model from stored data.

        For stored nodes, this reads from attributes and the npz file in repository.
        For unstored nodes, returns the in-memory properties.

        The reconstructed model is cached to avoid re-running validators on every access.
        """
        if self.is_stored:
            # Return cached model instance if available
            # Use getattr because when loading from DB, __init__ is not called
            if getattr(self, "_cached_model_instance", None) is not None:
                return self._cached_model_instance

            # Collect all attributes
            attributes = dict(self.base.attributes.all)

            # Remove npz metadata from attributes
            npz_metadata_keys = [
                key for key in attributes.keys() if key.startswith("shape|")
            ]
            for key in npz_metadata_keys:
                attributes.pop(key)

            # Load all array properties from npz file in one go
            npz_properties = self._load_properties_from_npz()
            attributes.update(npz_properties)

            # Handle kind-based decompression if needed
            if "kind_names" in attributes:
                from aiida_atomistic.data.structure.utils_kinds import (
                    rebuild_site_lists_from_kind_lists,
                )
                from aiida_atomistic.data.structure.utils import (
                    build_sites_from_expanded_properties,
                )

                attribute_lists_dict = rebuild_site_lists_from_kind_lists(
                    attributes, model_class=self._model
                )
                attributes = build_sites_from_expanded_properties(
                    attribute_lists_dict, model_class=self._model
                )
            else:
                from aiida_atomistic.data.structure.utils import (
                    build_sites_from_expanded_properties,
                )

                attributes = build_sites_from_expanded_properties(
                    attributes, model_class=self._model
                )

            # Create model instance and cache it
            model_instance = self._model(**attributes)
            self._cached_model_instance = model_instance
            return model_instance
        else:
            return self._properties

    @classmethod
    def from_builder(cls, builder: "StructureBuilder"):
        """Create a StructureData from a StructureBuilder."""
        from aiida_atomistic.data.structure.structure import StructureBuilder

        if not isinstance(builder, StructureBuilder):
            raise ValueError(
                f"Input builder should be of type StructureBuilder, not {type(builder)}"
            )
        return cls(**builder.to_dict())

    def to_builder(self) -> "StructureBuilder":
        """Convert to a mutable StructureBuilder."""
        return StructureBuilder(**self.to_dict())

    def get_value(self) -> "StructureBuilder":
        return self.to_builder()

    def __len__(self) -> int:
        """Return the number of sites in the structure."""
        return len(self.properties.sites)

    def __getitem__(self, index) -> "StructureData":
        """
        Return a new (unstored) :class:`StructureData` containing only the
        sites selected by ``index``.

        Supported index types:

        * **int** — single site, e.g. ``node[0]`` or ``node[-1]``
        * **slice** — contiguous or strided range, e.g. ``node[10:20]``
          or ``node[::2]``
        * **list / tuple of ints** — arbitrary selection, e.g.
          ``node[[0, 3, 7]]``
        * **numpy integer array** — same as list, e.g.
          ``node[np.array([0, 3, 7])]``

        Cell, pbc and all other global properties (``tot_charge``,
        ``tot_magnetization``, ``custom``, …) are preserved unchanged in the
        returned node.  Per-site global aggregates such as ``formula`` are
        recomputed automatically from the new site list.

        :param index: An ``int``, ``slice``, ``list``/``tuple`` of ints, or a
            1-D integer numpy array selecting the desired site indices.
        :return: A new, **unstored** :class:`StructureData` with the selected
            sites.  Call ``.store()`` if persistence is needed.
        :raises IndexError: If any index is out of range.
        :raises TypeError: If ``index`` is not one of the supported types.

        Examples::

            # Single site as a one-site StructureData
            one = node[0]

            # First ten sites
            first_ten = node[0:10]

            # Every other site
            even = node[::2]

            # Arbitrary selection, then store
            subset = node[[0, 5, 12]]
            subset.store()
        """
        import copy

        selected = _resolve_site_indices(self.properties.sites, index)
        new_dict = copy.deepcopy(self.to_dict())
        new_dict["sites"] = [
            s.model_dump(exclude_unset=True, exclude_none=True, warnings=False)
            if hasattr(s, "model_dump")
            else dict(s)
            for s in selected
        ]
        return StructureData(**new_dict)

    def __repr__(self) -> str:
        """Return a concise string representation of the structure."""
        from aiida_atomistic.data.structure.utils import get_structure_repr

        # Build UUID string
        if self.is_stored:
            uuid_str = f"<{self.__class__.__name__}: uuid: {self.uuid} (pk: {self.pk})>"
        else:
            uuid_str = f"<{self.__class__.__name__}: uuid: {self.uuid} (unstored)>"

        prop_repr_str = get_structure_repr(self)
        return uuid_str + f"\n {prop_repr_str.replace('ImmutableStructureModel', '')}"

    def __str__(self) -> str:
        """Return a string representation of the structure for print()."""
        return self.__repr__()

    def _validate(self) -> bool:
        """
        Validate the node.

        Check that npz metadata in attributes matches properties in npz file.
        """
        from aiida.common.exceptions import ValidationError

        # Get property names from npz file
        npz_properties = set(self._load_properties_from_npz().keys())

        # Get property names from attributes metadata
        attributes_properties = set(
            key[6:]  # Remove 'shape|' prefix (6 characters)
            for key in self.base.attributes.keys()
            if key.startswith("shape|")
        )

        if not attributes_properties:
            return super()._validate()

        if npz_properties != attributes_properties:
            raise ValidationError(
                f"Mismatch of npz properties and attributes metadata for "
                f"StructureData node (pk={self.pk}): "
                f"npz={npz_properties} vs attributes={attributes_properties}"
            )

        return super()._validate()


class StructureBuilder(GetterMixin, SetterMixin):
    _mutable = True
    _model = MutableStructureModel

    def __init__(self, sites: list[dict] = None, kinds: list[dict] = None, **kwargs):
        """
        Initialize a StructureBuilder instance.

        :param sites: list of site dictionaries
        :param kinds: list of kind dictionaries
        :param kwargs: Additional properties (pbc, cell, etc.)
        """
        from aiida_atomistic.data.structure.utils_kinds import sites_from_kinds

        # if both sites and kinds are provided, we use kinds and we print a warning
        # basically, we map kinds->sites, as the structure object is site-based
        if sites is not None and kinds is not None:
            warnings.warn(
                "Provided both `sites` and `kinds` information. "
                "Dropping the `sites` information and using only `kinds`."
            )
            sites = sites_from_kinds(kinds)
        elif kinds is not None:
            sites = sites_from_kinds(kinds)

        self._properties = self._model(sites=sites, **kwargs)
        super().__init__()

    @property
    def properties(self):
        return self._properties

    @classmethod
    def from_aiida(cls, aiida: "StructureData"):
        if not isinstance(aiida, StructureData):
            raise ValueError(
                f"Input aiida should be of type StructureData, not {type(aiida)}"
            )
        return cls(**aiida.to_dict())

    def to_aiida(self) -> "StructureData":
        return StructureData(**self.to_dict())

    def __len__(self) -> int:
        """Return the number of sites in the structure."""
        return len(self.properties.sites)

    def __getitem__(self, index) -> "StructureBuilder":
        """
        Return a new :class:`StructureBuilder` containing only the sites selected
        by ``index``.

        Supported index types:

        * **int** — single site, e.g. ``builder[0]`` or ``builder[-1]``
        * **slice** — contiguous or strided range, e.g. ``builder[10:20]``
          or ``builder[::2]``
        * **list / tuple of ints** — arbitrary selection, e.g.
          ``builder[[0, 3, 7]]``
        * **numpy integer array** — same as list, e.g.
          ``builder[np.array([0, 3, 7])]``

        Cell, pbc and all other global properties (``tot_charge``,
        ``tot_magnetization``, ``custom``, …) are preserved unchanged in the
        returned builder.  Per-site global aggregates such as ``formula`` are
        recomputed automatically from the new site list.

        .. note::
            This operates on the **site-based** representation.  If the
            original structure was built with ``kinds=``, the builder already
            holds the expanded site list, so slicing is always well-defined.

        :param index: An ``int``, ``slice``, ``list``/``tuple`` of ints, or a
            1-D integer numpy array selecting the desired site indices.
        :return: A new :class:`StructureBuilder` with the selected sites.
        :raises IndexError: If any index is out of range.
        :raises TypeError: If ``index`` is not one of the supported types.

        Examples::

            b = StructureBuilder(sites=[...], cell=..., pbc=...)

            # Single site
            one = b[0]

            # First ten sites
            first_ten = b[0:10]

            # Every other site
            even = b[::2]

            # Arbitrary selection
            subset = b[[0, 5, 12, 99]]
        """
        import copy

        selected = _resolve_site_indices(self.properties.sites, index)
        new_dict = copy.deepcopy(self.to_dict())
        new_dict["sites"] = [
            s.model_dump(exclude_unset=True, exclude_none=True, warnings=False)
            if hasattr(s, "model_dump")
            else dict(s)
            for s in selected
        ]
        return StructureBuilder(**new_dict)

    def __repr__(self) -> str:
        """Return a concise string representation of the structure."""

        from aiida_atomistic.data.structure.utils import get_structure_repr

        prop_repr_str = get_structure_repr(self)
        return (
            super().__repr__()
            + f"\n {prop_repr_str.replace('MutableStructureModel', '')}"
        )

    def __str__(self) -> str:
        """Return a string representation of the structure for print()."""
        return self.__repr__()
