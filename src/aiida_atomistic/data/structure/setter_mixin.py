import typing as t
import numpy as np

from aiida.common.constants import elements

from aiida_atomistic.data.structure.site import Site
from aiida_atomistic.data.structure.hubbard_mixin import HubbardSetterMixin

try:
    import ase  # noqa: F401

    has_ase = True
    ASE_ATOMS_TYPE = ase.Atoms
except ImportError:
    has_ase = False

    ASE_ATOMS_TYPE = t.Any

try:
    import pymatgen.core as core  # noqa: F401

    has_pymatgen = True
    PYMATGEN_MOLECULE = core.structure.Molecule
    PYMATGEN_STRUCTURE = core.structure.Structure
except ImportError:
    has_pymatgen = False

    PYMATGEN_MOLECULE = t.Any
    PYMATGEN_STRUCTURE = t.Any

_MASS_THRESHOLD = 1.0e-3
# Threshold to check if the sum is one or not
_SUM_THRESHOLD = 1.0e-6
# Default cell
_DEFAULT_CELL = ((0, 0, 0),) * 3

_DEFAULT_PROPERTIES = {
    "pbc",
    "cell",
    "sites",
    "masses",
    "kinds",
    "symbols",
    "positions",
    "weights",
    "custom",  # experimental
}

_valid_symbols = tuple(i["symbol"] for i in elements.values())
_atomic_masses = {el["symbol"]: el["mass"] for el in elements.values()}
_atomic_numbers = {data["symbol"]: num for num, data in elements.items()}

_DEFAULT_VALUES = {
    "masses": 0,
    "charges": 0,
    "magmoms": [0, 0, 0],
    "hubbard": None,
    "weights": (1,),
}

_DEFAULT_THRESHOLDS = {
    "charges": 0.1,
    "masses": 1e-4,
    "magmoms": 1e-4,  # _MAGMOM_THRESHOLD
}


class SetterMixin(HubbardSetterMixin):
    def _validate_properties(
        self,
    ):
        """Validate the structure.

        This method performs a series of checks to ensure that the structure's properties are consistent and valid.
        It raises a ValueError if any inconsistency is found.

        Returns:
            None
        """
        return self.properties.validate_instance()

    def set_pbc(self, value):
        """Set the periodic boundary conditions."""
        from aiida_atomistic.data.structure.utils import _get_valid_pbc

        the_pbc = _get_valid_pbc(value)
        self.properties.pbc = the_pbc

    def set_cell(self, value):
        """Set the cell."""
        from aiida_atomistic.data.structure.utils import _get_valid_cell

        the_cell = _get_valid_cell(value)
        self.properties.cell = the_cell

    def set_cell_lengths(self, value):
        raise NotImplementedError("This method is not implemented yet")

    def set_cell_angles(self, value):
        raise NotImplementedError("This method is not implemented yet")

    def update_sites(self, site_indices: t.Union[list[int], int], **kwargs):
        """
        Update the site at the given index.
        """
        for key, value in kwargs.items():
            if isinstance(site_indices, int):
                setattr(self.properties.sites[site_indices], key, value)
            elif isinstance(site_indices, list):
                for site_index in site_indices:
                    setattr(self.properties.sites[site_index], key, value)

        return

    def update_kind(self, kind_name, **kwargs):
        """
        Update all sites with the given kind name.
        """
        if not self.kinds:
            raise ValueError(
                "You cannot update a kind if the structure has no kinds defined. Please use the `update_sites` method."
            )

        kind_indices = [
            i
            for i, site in enumerate(self.properties.sites)
            if site.kind_name == kind_name
        ]
        self.update_sites(kind_indices, **kwargs)
        return

    def append_atom(self, atom: t.Union[Site, dict] = None, index: int = -1, **kwargs):
        """Append an atom to the structure.

        Args:
            atom: Site object or dictionary with site properties. If None, kwargs are used.
            index: Position where to insert the atom. Default -1 (append at end).
            **kwargs: Site properties (symbol, position, charge, magmom, etc.) if atom is None.

        Examples:
            # Using kwargs (recommended)
            builder.append_atom(symbol="Fe", position=[0, 0, 0], magmom=[0, 0, 2.2])

            # Using dict
            builder.append_atom({"symbol": "Fe", "position": [0, 0, 0]})

            # Using Site object
            site = Site(symbol="Fe", position=[0, 0, 0])
            builder.append_atom(site)
        """
        # Determine the site data to use
        if atom is None:
            if not kwargs:
                raise ValueError(
                    "Must provide either 'atom' parameter or keyword arguments"
                )
            new_site = Site(**kwargs)
        elif isinstance(atom, dict):
            if kwargs:
                raise ValueError(
                    "Cannot provide both 'atom' as dict and keyword arguments"
                )
            new_site = Site(**atom)
        elif isinstance(atom, Site):
            if kwargs:
                raise ValueError(
                    "Cannot provide both 'atom' as Site and keyword arguments"
                )
            new_site = atom
        else:
            raise TypeError(
                f"atom must be Site, dict, or None (with kwargs), not {type(atom)}"
            )

        if len(self.properties.sites) == 0:
            self.properties.sites.insert(-1, new_site)
            return

        # check that the matrix is not singular. If it is, raise an error.
        # check to be done in the core.
        for site_position in self.properties.positions:
            if (
                np.linalg.norm(np.array(new_site.position) - np.array(site_position))
                < 1e-3
            ):
                raise ValueError(
                    "You cannot define two different sites to be in the same position!"
                )

        if len(self.properties.sites) < index:
            raise IndexError(
                f"index {index} out of range: the structure has only {len(self.properties.sites)} sites."
            )
        else:
            index = index if index >= 0 else len(self.properties.sites)
            self.properties.sites.insert(index, new_site)
        return

    def pop_atom(self, index=-1):
        # If no index is provided, pop the last item
        self.properties.sites.pop(index)
        return

    def clear_sites(
        self,
    ):
        """Clear the sites, i.e. every property except pbc, cell and custom."""
        self.properties.sites = []
        return

    def remove_property(self, property_name):
        """Clear the given property."""

        if hasattr(self.properties, property_name):
            setattr(self.properties, property_name, None)

            return

        for site in self.properties.sites:
            if hasattr(site, property_name):
                setattr(site, property_name, None)
        return

    # setter and remove methods for specific properties
    def set_charges(self, charges: np.ndarray[float]):
        if len(charges) != len(self.properties.sites):
            raise ValueError(
                f"The length of the charges list ({len(charges)}) does not match the number of sites ({len(self.properties.sites)})."
            )
        for site, charge in zip(self.properties.sites, charges):
            site.charge = charge
        return

    def remove_charges(self):
        self.remove_property("charge")
        return

    def set_masses(self, masses: np.ndarray[float]):
        if len(masses) != len(self.properties.sites):
            raise ValueError(
                f"The length of the masses list ({len(masses)}) does not match the number of sites ({len(self.properties.sites)})."
            )
        for site, mass in zip(self.properties.sites, masses):
            site.mass = mass
        return

    def remove_masses(self):
        self.remove_property("mass")
        return

    def set_magmoms(self, magmoms: np.ndarray[np.ndarray[float]]):
        # if defined magnetization or tot_magnetization, raise an error
        if len(magmoms) != len(self.properties.sites):
            raise ValueError(
                f"The length of the magmoms list ({len(magmoms)}) does not match the number of sites ({len(self.properties.sites)})."
            )
        for site, magmom in zip(self.properties.sites, magmoms):
            site.magmom = magmom
        return

    def remove_magmoms(self):
        self.remove_property("magmom")
        return

    def set_magnetizations(self, magnetizations: np.ndarray[float]):
        if len(magnetizations) != len(self.properties.sites):
            raise ValueError(
                f"The length of the magnetizations array ({len(magnetizations)}) does not match the number of sites ({len(self.properties.sites)})."
            )
        for site, magnetization in zip(self.properties.sites, magnetizations):
            site.magnetization = magnetization
        return

    def remove_magnetizations(self):
        self.remove_property("magnetization")
        return

    def set_weights(self, weights: np.ndarray[np.ndarray[float]]):
        if len(weights) != len(self.properties.sites):
            raise ValueError(
                f"The length of the weights array ({len(weights)}) does not match the number of sites ({len(self.properties.sites)})."
            )
        for site, weight in zip(self.properties.sites, weights):
            site.weight = weight
        return

    def remove_weights(self):
        self.remove_property("weight")
        return

    def set_tot_charge(self, value: float):
        """Set the total charge of the cell."""
        self.properties.tot_charge = value
        return

    def remove_tot_charge(self):
        self.remove_property("tot_charge")
        return

    def set_tot_magnetization(self, value: float):
        """Set the total magnetic moment of the cell."""
        self.properties.tot_magnetization = value
        return

    def remove_hubbard(self):
        self.remove_property("hubbard")
        return

    def set_kind_names(self, value: list):
        if len(value) != len(self.properties.sites):
            raise ValueError(
                f"The length of the kind_names list ({len(value)}) does not match the number of sites ({len(self.properties.sites)})."
            )
        for site, kind_name in zip(self.properties.sites, value):
            site.kind_name = kind_name
        return

    def remove_kind_names(self):
        self.remove_property("kind_name")
        return

    def set_custom(self, value: dict):
        """Set the custom properties."""
        if not self.properties.custom:
            self.properties.custom = {}
        self.properties.custom.update(value)
        return

    def remove_custom(self, keys: t.List[str] = None):
        """Remove the custom properties.

        If keys is None, remove all custom properties.
        If keys is provided, remove only the specified keys.
        """

        if not self.properties.custom:
            return
        if keys:
            for key in keys:
                if key in self.properties.custom:
                    del self.properties.custom[key]
        else:
            self.remove_property("custom")
        return
