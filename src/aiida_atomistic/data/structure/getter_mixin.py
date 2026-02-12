import copy
import json
import typing as t
import numpy as np

from aiida import orm
from aiida.common.constants import elements

from aiida_atomistic.data.structure.site import Site, FrozenSite
from aiida_atomistic.data.structure.hubbard_mixin import (
    HubbardGetterMixin,
)
from aiida_atomistic.data.structure.utils import _get_computed_properties_from_model

try:
    import ase  # noqa: F401
    from ase import io as ase_io

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

_valid_symbols = tuple(i["symbol"] for i in elements.values())
_atomic_masses = {el["symbol"]: el["mass"] for el in elements.values()}
_atomic_numbers = {data["symbol"]: num for num, data in elements.items()}


class GetterMixin(HubbardGetterMixin):

    # Start redundant properties: This is mainly for make easier migration of plugins.
    @property
    def cell(self):
        return self.properties.cell

    @property
    def pbc(self):
        return self.properties.pbc

    @property
    def sites(self):
        return self.properties.sites

    @property
    def kinds(self):
        return self.properties.kinds

    @property
    def is_alloy(self):
        return self.properties.is_alloy

    @property
    def has_vacancies(self):
        return self.properties.has_vacancies

    @property
    def formula(self):
        return self.properties.formula
    # End redundant properties

    @classmethod
    def get_supported_properties(cls):
        """
        Get a dictionary of global and site properties that can be set
        for this structure.
        """
        structure_fields = set(cls._model.model_fields.keys())
        site_fields = set(Site.model_fields.keys())

        return {
            'global': structure_fields,
            'site': site_fields
        }

    @classmethod
    def get_computed_properties(cls):
        """
        Get a dictionary of computed properties that can be set
        for this structure.
        """
        return set(_get_computed_properties_from_model(cls._model))

    def get_defined_properties(self, exclude_computed: bool = False):
        """
            Retrieve the defined properties of the structure, categorized into direct, computed, and site-specific properties.

            Args:
                exclude_computed (bool): If False, all properties will be returned, including those computed after the initialization (the pydantic computed fields).
                exclude_defaults (bool): If True, properties with default values will be excluded from the result.
        """
        return set(self.properties.model_dump(exclude_unset=True, exclude_none=True, warnings=False).keys()).difference(set(self._model.model_computed_fields.keys()) if exclude_computed else set())


    def get_kind_names(self):
        """Return a list of the kind names defined in this structure."""
        return None if self.properties.kind_names is None else list(set(self.properties.kind_names))

    def get_kind(self, kind_name: str = None):
        """Return a given kind."""
        if not self.kinds:
            return None
        for kind in self.kinds:
            if kind.kind_name == kind_name:
                return kind

    @property
    def is_collinear(self):
        # if not magmoms, is can be collinear if magnetizations are provided (just quantum number)
        # if magmoms, we check that the rank of the magmoms matrix is one (if not, it is not collinear)
        if self.properties.magmoms is None:
            return False
        if self.properties.magnetizations is not None:
            return True
        return np.linalg.matrix_rank(self.properties.magmoms) == 1


    # initialization methods
    @classmethod
    def from_ase(
        cls,
        aseatoms: ASE_ATOMS_TYPE,
    ):
        """Load the structure from a ASE object"""

        if not has_ase:
            raise ImportError("The ASE package cannot be imported.")

        if not cls._mutable:
            SiteClass = FrozenSite
        else:
            SiteClass = Site

        # Read the ase structure
        data = {}
        data["cell"] = aseatoms.cell.array.tolist()
        data["pbc"] = aseatoms.pbc.tolist()

        data["sites"] = []
        # self.clear_kinds()  # This also calls clear_sites
        for atom in aseatoms:
            tag_to_kind_name=len(set(aseatoms.get_tags())) > 1

            new_site = SiteClass.from_ase_atom(aseatom=atom, tag_to_kind_name=tag_to_kind_name)
            data["sites"].append(new_site.model_dump())


        structure = cls(**data)

        return structure

    @classmethod
    def from_file(
        cls,
        filename,
        format="cif",
        parser:str="ase",
        **kwargs):
        """Load the structure from a file.

        It is possible to specify the parser between ase or pymatgen, default is ase.
        """

        if format == 'mcif' or '.mcif' in filename or parser == "pymatgen":
            # in this case, we use pymatgen parser, because the ase one does not work properly for now.
            from pymatgen.io.cif import CifParser
            parser  = CifParser(filename)
            mcif_structure   = parser.parse_structures(**kwargs)[0]
            return cls.from_pymatgen(pymatgen_obj=mcif_structure)
        else:
            ase_read = ase_io.read(filename, format=format, **kwargs)
            return cls.from_ase(aseatoms=ase_read)

    @classmethod
    def from_pymatgen(
        cls,
        pymatgen_obj: t.Union[PYMATGEN_MOLECULE, PYMATGEN_STRUCTURE],
        **kwargs,
    ):
        """Load the structure from a pymatgen object.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        if not has_pymatgen:
            raise ImportError("The pymatgen package cannot be imported.")

        if isinstance(pymatgen_obj, PYMATGEN_MOLECULE):
            structure = cls._from_pymatgen_molecule(pymatgen_obj, **kwargs)
        else:
            structure = cls._from_pymatgen_structure(pymatgen_obj, **kwargs)

        return structure

    @classmethod
    def _from_pymatgen_molecule(
        cls,
        mol: PYMATGEN_MOLECULE,
        margin=5,
        ):
        """Load the structure from a pymatgen Molecule object.

        :param margin: the margin to be added in all directions of the
            bounding box of the molecule.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        box = [
            max(x.coords.tolist()[0] for x in mol.properties.sites)
            - min(x.coords.tolist()[0] for x in mol.properties.sites)
            + 2 * margin,
            max(x.coords.tolist()[1] for x in mol.properties.sites)
            - min(x.coords.tolist()[1] for x in mol.properties.sites)
            + 2 * margin,
            max(x.coords.tolist()[2] for x in mol.properties.sites)
            - min(x.coords.tolist()[2] for x in mol.properties.sites)
            + 2 * margin,
        ]
        structure = cls._from_pymatgen_structure(mol.get_boxed_structure(*box))
        structure.properties.pbc = [False, False, False]

        return structure

    @classmethod
    def _from_pymatgen_structure(
        cls,
        struct: PYMATGEN_STRUCTURE,
        ):
        """Load the structure from a pymatgen Structure object.

        .. note:: periodic boundary conditions are set to True in all
            three directions.
        .. note:: Requires the pymatgen module (version >= 3.3.5, usage
            of earlier versions may cause errors).

        :raise ValueError: if there are partial occupancies together with spins.
        """

        def build_kind_name(species_and_occu):
            """Build a kind name from a pymatgen Composition, including an additional ordinal if spin is included,
            e.g. it returns '<specie>1' for an atom with spin < 0 and '<specie>2' for an atom with spin > 0,
            otherwise (no spin) it returns None

            :param species_and_occu: a pymatgen species and occupations dictionary
            :return: a string representing the kind name or None
            """
            species = list(species_and_occu.keys())
            occupations = list(species_and_occu.values())

            # As of v2023.9.2, the ``properties`` argument is removed and the ``spin`` argument should be used.
            # See: https://github.com/materialsproject/pymatgen/commit/118c245d6082fe0b13e19d348fc1db9c0d512019
            # The ``spin`` argument was introduced in v2023.6.28.
            # See: https://github.com/materialsproject/pymatgen/commit/9f2b3939af45d5129e0778d371d814811924aeb6
            has_spin_attribute = hasattr(species[0], "_spin")

            if has_spin_attribute:
                has_spin = any(specie.spin != 0 for specie in species)
            else:
                has_spin = any(
                    specie.as_dict().get("properties", {}).get("spin", 0) != 0
                    for specie in species
                )

            has_partial_occupancies = len(occupations) != 1 or occupations[0] != 1.0

            if has_partial_occupancies and has_spin:
                raise ValueError(
                    "Cannot set partial occupancies and spins at the same time"
                )

            if has_spin:
                from aiida_atomistic.data.structure.utils import create_automatic_kind_name
                symbols = [specie.symbol for specie in species]
                kind_name = create_automatic_kind_name(symbols, occupations)

                # If there is spin, we can only have a single specie, otherwise we would have raised above
                specie = species[0]
                if has_spin_attribute:
                    spin = specie.spin
                else:
                    spin = specie.as_dict().get("properties", {}).get("spin", 0)

                if spin < 0:
                    kind_name += "1"
                else:
                    kind_name += "2"

                return kind_name

            return None

        inputs = {}
        inputs["cell"] = struct.lattice.matrix.tolist()
        inputs["pbc"] = [True, True, True]
        # self.clear_kinds()

        inputs["sites"] = []
        sites_collection = struct.properties["sites"] if "sites" in struct.properties.keys() else struct.sites
        for site in sites_collection:

            site_info = {
                "symbol": site.specie.symbol,
                "mass": site.species.weight,
                "position": site.coords.tolist(),
                'magmom': site.properties.get("magmom").moment if "magmom" in site.properties.keys() else None
            }


            if site.properties.get('kinds', None) is not None:
                site_info["kind_name"] = site.properties.get('kinds').replace("+", "").replace("-", "")

            if bool(site.properties.get('charge', None)):
                site_info["charge"] = site.properties.get("charge")

            if site.properties.get('magmom', None) is not None:
                magmom = site.properties.get("magmom").moment
                if isinstance(magmom, (int, float)):
                    if magmom != 0:
                        site_info['magnetization'] = magmom
                elif isinstance(magmom, (list, np.ndarray)):
                    if np.linalg.norm(magmom) > 0:
                        site_info['magmom'] = magmom

            inputs["sites"].append(site_info)

        structure = cls(**inputs)

        return structure

    def validate_kinds(self, threshold: dict = {}):
        """Validate that the kinds defined in the structure match the ones generated from the sites.
        :param threshold: Threshold for grouping sites into kinds. Should be a dictionary specifying thresholds for specific properties.
        :type threshold: dict, optional. The default values are taken from Site.get_default_thresholds()

        :raises ValueError: if the kinds defined in the structure do not match the ones generated from the sites.
        """

        from aiida_atomistic.data.structure.utils_kinds import generate_kinds, check_kinds_match

        if not self.kinds:
            raise ValueError("No kinds defined in the structure.")

        # defaul thresholds
        all_thresholds = Site.get_default_thresholds()

        # update the thresholds with the user-defined ones
        all_thresholds.update(threshold)

        kinds = generate_kinds(self, threshold=all_thresholds)
        check_kinds = check_kinds_match(self, kinds)

        if not check_kinds:
            raise ValueError("The kinds defined in the structure do not match the generated kinds from the sites. Please run the 'to_kinds' method to see the expected kinds.")

        return True

    # TO methods:
    def to_kinds(self, threshold: dict = {}, store_provenance: bool=True):
        """
        Convert the structure to a kinds-based representation.

        :param threshold: Threshold for grouping sites into kinds. Should be a dictionary specifying thresholds for specific properties.
        :type threshold: dict, optional. The default values are taken from Site.get_default_thresholds()
        :type store_provenance: bool, optional
        :return: The structure as a dictionary with kinds.
        :rtype: dict
        """

        from aiida_atomistic.data.structure.utils_kinds import to_kinds as to_kinds_function
        from aiida_atomistic.data.structure.structure import StructureBuilder, StructureData

        # defaul thresholds
        all_thresholds = Site.get_default_thresholds()

        # update the thresholds with the user-defined ones
        all_thresholds.update(threshold)

        if isinstance(self, StructureBuilder):
            return to_kinds_function(self, threshold=all_thresholds)
        elif isinstance(self, StructureData):
            from aiida.engine import calcfunction
            return calcfunction(to_kinds_function)(self, threshold=orm.Dict(all_thresholds), metadata={'store_provenance': store_provenance})


    def to_dict(self):
            """
            Convert the structure to a dictionary representation.

            :return: The structure as a dictionary.
            :rtype: dict
            """
            exclude = set(self.properties.model_computed_fields.keys())
            dict_repr = copy.deepcopy(self.properties.model_dump(exclude_unset=True, exclude_none=True, warnings=False, exclude=exclude))

            return dict_repr

    def to_cif(self, converter="ase", store=False, **kwargs):
        """Creates :py:class:`aiida.orm.nodes.data.cif.CifData`.

        :param converter: specify the converter. Default 'ase'.
        :param store: If True, intermediate calculation gets stored in the
            AiiDA database for record. Default False.
        :return: :py:class:`aiida.orm.nodes.data.cif.CifData` node.
        """
        from aiida.tools.data import structure as structure_tools

        param = orm.Dict(kwargs)
        try:
            conv_f = getattr(structure_tools, f"_get_cif_{converter}_inline")
        except AttributeError:
            raise ValueError(f"No such converter '{converter}' available")
        ret_dict = conv_f(
            struct=self, parameters=param, metadata={"store_provenance": store}
        )
        return ret_dict["cif"]

    def get_description(self):
        """Returns a string with infos retrieved from StructureData node's properties

        :param self: the StructureData node
        :return: retsrt: the description string
        """
        return self.get_formula(mode="hill_compact")

    def get_composition(self, mode="full"):
        """Returns the chemical composition of this structure as a dictionary,
        where each key is the kind symbol (e.g. H, Li, Ba),
        and each value is the number of occurences of that element in this
        structure.

        :param mode: Specify the mode of the composition to return. Choose from ``full``, ``reduced`` or ``fractional``.
            For example, given the structure with formula Ba2Zr2O6, the various modes operate as follows.
            ``full``: The default, the counts are left unnnormalized.
            ``reduced``: The counts are renormalized to the greatest common denominator.
            ``fractional``: The counts are renormalized such that the sum equals 1.

        :returns: a dictionary with the composition
        """
        import numpy as np

        symbols_list = self.properties.symbols

        symbols_set = set(symbols_list)

        if mode == "full":
            return {symbol: symbols_list.count(symbol) for symbol in symbols_set}

        if mode == "reduced":
            gcd = np.gcd.reduce([symbols_list.count(symbol) for symbol in symbols_set])
            return {
                symbol: (symbols_list.count(symbol) / gcd) for symbol in symbols_set
            }

        if mode == "fractional":
            sum_comp = sum(symbols_list.count(symbol) for symbol in symbols_set)
            return {
                symbol: symbols_list.count(symbol) / sum_comp for symbol in symbols_set
            }

        raise ValueError(
            f"mode `{mode}` is invalid, choose from `full`, `reduced` or `fractional`."
        )

    def to_ase(self):
        """Get the ASE object.
        Requires to be able to import ase.

        :return: an ASE object corresponding to this
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        object.

        .. note:: If any site is an alloy or has vacancies, a ValueError
            is raised (from the site.to_ase() routine).
        """
        if not has_ase:
            raise ImportError("The ASE package cannot be imported.")

        return self._get_object_ase()

    def to_pymatgen(self, **kwargs):
        """Get pymatgen object. Returns pymatgen Structure for structures with periodic boundary conditions
        (in 1D, 2D, 3D) and Molecule otherwise.
        :param add_spin: True to add the spins to the pymatgen structure.
        Default is False (no spin added).

        .. note:: The spins are set according to the following rule:

            * if the kind name ends with 1 -> spin=+1

            * if the kind name ends with 2 -> spin=-1

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        if not has_pymatgen:
            raise ImportError("The pymatgen package cannot be imported.")

        return self._get_object_pymatgen(**kwargs)

    def to_file(self, filename=None, format="cif"):

        """Writes the structure to a file.

        Args:
            filename (_type_, optional): defaults to None.
            format (str, optional): defaults to "cif".

        Raises:
            ValueError: should provide a filename different from None.
        """
        if not has_ase:
            raise ImportError("The ASE package cannot be imported.")

        if not filename:
            raise ValueError("Please provide a valid filename.")

        aseatoms = self.to_ase()
        ase_io.write(filename, aseatoms, format=format)

        return

    '''def to_legacy(self) -> LegacyStructureData:

        """
        Returns: orm.StructureData object, used for backward compatibility.
        """
        if not has_ase:
            raise ImportError("The ASE package cannot be imported.")

        aseatoms = self.to_ase()

        return LegacyStructureData(ase=aseatoms)
    '''

    def get_pymatgen_structure(self, **kwargs):
        """Get the pymatgen Structure object with any PBC, provided the cell is not singular.
        :param add_spin: True to add the spins to the pymatgen structure.
        Default is False (no spin added).

        .. note:: The spins are set according to the following rule:

            * if the kind name ends with 1 -> spin=+1

            * if the kind name ends with 2 -> spin=-1

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).

        :return: a pymatgen Structure object corresponding to this
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        object.
        :raise ValueError: if the cell is singular, e.g. when it has not been set.
            Use `get_pymatgen_molecule` instead, or set a proper cell.
        """
        return self._get_object_pymatgen_structure(**kwargs)

    def get_pymatgen_molecule(self):
        """Get the pymatgen Molecule object.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).

        :return: a pymatgen Molecule object corresponding to this
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        object.
        """
        return self._get_object_pymatgen_molecule()

    def _prepare_xsf(self, main_file_name=""):
        """Write the given structure to a string of format XSF (for XCrySDen)."""
        if self.is_alloy or self.has_vacancies:
            raise NotImplementedError(
                "XSF for alloys or systems with vacancies not implemented."
            )

        sites = self.properties.sites

        return_string = "CRYSTAL\nPRIMVEC 1\n"
        for cell_vector in self.properties.cell:
            return_string += " ".join([f"{i:18.10f}" for i in cell_vector])
            return_string += "\n"
        return_string += "PRIMCOORD 1\n"
        return_string += f"{int(len(sites))} 1\n"
        for site in sites:
            # I checked above that it is not an alloy, therefore I take the
            # first symbol
            return_string += (
                f"{_atomic_numbers[site.symbols]} "
            )
            return_string += "%18.10f %18.10f %18.10f\n" % tuple(site.position)
        return return_string.encode("utf-8"), {}

    def _prepare_cif(self, main_file_name=""):
        """Write the given structure to a string of format CIF."""
        from aiida.orm import CifData

        cif = CifData(ase=self.to_ase())
        return cif._prepare_cif()

    def _prepare_chemdoodle(self, main_file_name=""):
        """Write the given structure to a string of format required by ChemDoodle."""
        from itertools import product
        from aiida_atomistic.data.structure.utils import atom_kinds_to_html

        import numpy as np

        supercell_factors = [1, 1, 1]

        # Get cell vectors and atomic position
        lattice_vectors = np.array(self.base.attributes.get("cell"))
        base_sites = self.sites

        start1 = -int(supercell_factors[0] / 2)
        start2 = -int(supercell_factors[1] / 2)
        start3 = -int(supercell_factors[2] / 2)

        stop1 = start1 + supercell_factors[0]
        stop2 = start2 + supercell_factors[1]
        stop3 = start3 + supercell_factors[2]

        grid1 = range(start1, stop1)
        grid2 = range(start2, stop2)
        grid3 = range(start3, stop3)

        atoms_json = []

        # Manual recenter of the structure
        center = (lattice_vectors[0] + lattice_vectors[1] + lattice_vectors[2]) / 2.0

        for ix, iy, iz in product(grid1, grid2, grid3):
            for base_site in base_sites:
                shift = (
                    ix * lattice_vectors[0]
                    + iy * lattice_vectors[1]
                    + iz * lattice_vectors[2]
                    - center
                ).tolist()

                kind_name = base_site.kinds
                kind_string = base_site.symbols

                atoms_json.append(
                    {
                        "l": kind_string,
                        "x": np.array(base_site.positions[0]) + shift[0],
                        "y": np.array(base_site.positions[1]) + shift[1],
                        "z": np.array(base_site.positions[2]) + shift[2],
                        "atomic_elements_html": atom_kinds_to_html(kind_string),
                    }
                )

        cell_json = {
            "t": "UnitCell",
            "i": "s0",
            "o": (-center).tolist(),
            "x": (lattice_vectors[0] - center).tolist(),
            "y": (lattice_vectors[1] - center).tolist(),
            "z": (lattice_vectors[2] - center).tolist(),
            "xy": (lattice_vectors[0] + lattice_vectors[1] - center).tolist(),
            "xz": (lattice_vectors[0] + lattice_vectors[2] - center).tolist(),
            "yz": (lattice_vectors[1] + lattice_vectors[2] - center).tolist(),
            "xyz": (
                lattice_vectors[0] + lattice_vectors[1] + lattice_vectors[2] - center
            ).tolist(),
        }

        return_dict = {"s": [cell_json], "m": [{"a": atoms_json}], "units": "&Aring;"}

        return json.dumps(return_dict).encode("utf-8"), {}

    def _prepare_xyz(self, main_file_name=""):
        """Write the given structure to a string of format XYZ."""
        if self.is_alloy or self.has_vacancies:
            raise NotImplementedError(
                "XYZ for alloys or systems with vacancies not implemented."
            )

        sites = self.properties.sites
        cell = self.properties.cell

        return_list = [f"{len(sites)}"]
        return_list.append(
            'Lattice="{} {} {} {} {} {} {} {} {}" pbc="{} {} {}"'.format(
                cell[0][0],
                cell[0][1],
                cell[0][2],
                cell[1][0],
                cell[1][1],
                cell[1][2],
                cell[2][0],
                cell[2][1],
                cell[2][2],
                self.properties.pbc[0],
                self.properties.pbc[1],
                self.properties.pbc[2],
            )
        )
        for site in sites:
            # I checked above that it is not an alloy, therefore I take the
            # first symbol
            return_list.append(
                "{:6s} {:18.10f} {:18.10f} {:18.10f}".format(
                    site.symbols,
                    site.position[0],
                    site.position[1],
                    site.position[2],
                )
            )

        return_string = "\n".join(return_list)
        return return_string.encode("utf-8"), {}

    def _parse_xyz(self, inputstring):
        """Read the structure from a string of format XYZ."""
        from aiida.tools.data.structure import xyz_parser_iterator

        # idiom to get to the last block
        atoms = None
        for _, _, atoms in xyz_parser_iterator(inputstring):
            pass

        if atoms is None:
            raise TypeError("The data does not contain any XYZ data")

        #self.clear_kinds()
        self.properties.pbc = (False, False, False)

        for sym, position in atoms:
            self.add_atom(atom_info={'symbols':sym, 'positions':position})

    def _adjust_default_cell(
        self, vacuum_factor=1.0, vacuum_addition=10.0, pbc=(False, False, False)
    ):
        """If the structure was imported from an xyz file, it lacks a cell.
        This method will adjust the cell
        """
        import numpy as np

        def get_extremas_from_positions(positions):
            """Returns the minimum and maximum value for each dimension in the positions given"""
            return list(
                zip(*[(min(values), max(values)) for values in zip(*positions)])
            )

        # Calculating the minimal cell:
        positions = np.array([site.positions for site in self.properties.sites])
        position_min, _ = get_extremas_from_positions(positions)

        # Translate the structure to the origin, such that the minimal values in each dimension
        # amount to (0,0,0)
        positions -= position_min
        for index, site in enumerate(self.sites):
            site.positions = list(positions[index])

        # The orthorhombic cell that (just) accomodates the whole structure is now given by the
        # extremas of position in each dimension:
        minimal_orthorhombic_cell_dimensions = np.array(
            get_extremas_from_positions(positions)[1]
        )
        minimal_orthorhombic_cell_dimensions = np.dot(
            vacuum_factor, minimal_orthorhombic_cell_dimensions
        )
        minimal_orthorhombic_cell_dimensions += vacuum_addition

        # Transform the vector (a, b, c ) to [[a,0,0], [0,b,0], [0,0,c]]
        newcell = np.diag(minimal_orthorhombic_cell_dimensions)
        self.set_cell(newcell.tolist())

        # Now set PBC (checks are done in set_pbc, no need to check anything here)
        self.set_pbc(pbc)

        return self

    def _get_object_phonopyatoms(self):
        """Converts StructureData to PhonopyAtoms

        :return: a PhonopyAtoms object
        """
        from phonopy.structure.atoms import PhonopyAtoms

        atoms = PhonopyAtoms(
            symbols = self.properties.symbols,
            masses = self.properties.masses,
            magnetic_moments = self.properties.magmoms,
            positions = self.properties.positions,
            cell = self.cell,
            pbc = self.pbc,
        )

        return atoms

    def _get_object_ase(self):
        """Converts
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        to ase.Atoms

        :return: an ase.Atoms object
        """
        import ase

        asecell = ase.Atoms(
            cell=self.properties.cell,
            pbc=self.properties.pbc,
            )

        for site in self.properties.sites:
            asecell.append(site.to_ase())

        # asecell.set_initial_charges(self.get_site_property("charge"))

        return asecell

    def _get_object_pymatgen(self, **kwargs):
        """Converts
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        to pymatgen object

        :return: a pymatgen Structure for structures with periodic boundary
            conditions (in three dimensions) and Molecule otherwise

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors).
        """
        if any(self.properties.pbc):
            return self._get_object_pymatgen_structure(**kwargs)

        return self._get_object_pymatgen_molecule(**kwargs)

    def _get_object_pymatgen_structure(self, **kwargs):
        """Converts
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        to pymatgen Structure object
        :param add_spin: True to add the spins to the pymatgen structure.
        Default is False (no spin added).

        .. note:: The spins are set according to the following rule:

            * if the kind name ends with 1 -> spin=+1

            * if the kind name ends with 2 -> spin=-1

        :return: a pymatgen Structure object corresponding to this
          :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
          object
        :raise ValueError: if the cell is not set (i.e. is the default one);
          if there are partial occupancies together with spins
          (defined by kind names ending with '1' or '2').

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors)
        """
        from pymatgen.core.lattice import Lattice
        from pymatgen.core.periodic_table import Specie
        from pymatgen.core.structure import Structure

        species = []
        additional_kwargs = {}

        lattice = Lattice(matrix=self.properties.cell, pbc=self.properties.pbc)

        if kwargs.pop("add_spin", False) and any(
            n.endswith("1") or n.endswith("2") for n in self.get_kind_names()
        ):
            # case when spins are defined -> no partial occupancy allowed

            oxidation_state = 0  # now I always set the oxidation_state to zero
            for site in self.properties.sites:
                kind = site.kinds
                if len(kind.symbols) != 1 or (
                    len(kind.weights) != 1 or sum(kind.weights) < 1.0
                ):
                    raise ValueError(
                        "Cannot set partial occupancies and spins at the same time"
                    )
                spin = (
                    -1
                    if site.kinds.endswith("1")
                    else 1
                    if site.kinds.endswith("2")
                    else 0
                )
                try:
                    specie = Specie(
                        kind.symbols[0], oxidation_state, properties={"spin": spin}
                    )
                except TypeError:
                    # As of v2023.9.2, the ``properties`` argument is removed and the ``spin`` argument should be used.
                    # See: https://github.com/materialsproject/pymatgen/commit/118c245d6082fe0b13e19d348fc1db9c0d512019
                    # The ``spin`` argument was introduced in v2023.6.28.
                    # See: https://github.com/materialsproject/pymatgen/commit/9f2b3939af45d5129e0778d371d814811924aeb6
                    specie = Specie(kind.symbols[0], oxidation_state, spin=spin)
                species.append(specie)
        else:
            # case when no spin are defined
            for site in self.properties.sites:
                kind = site.kind_name
                specie = Specie(
                    site.symbol,
                    site.charge,
                )  # spin)
                species.append(specie)
            # if any(
            #    create_automatic_kind_name(self.get_kind(name).symbols, self.get_kind(name).weights) != name
            #    for name in self.get_site_property("kinds")
            # ):
            # add "kinds" as a properties to each site, whenever
            # the kinds cannot be automatically obtained from the symbols
            additional_kwargs["site_properties"] = {
                "kinds": self.properties.kind_names,
                "charge": self.properties.charges,
                "magmom": self.properties.magmoms
            }

        if kwargs:
            raise ValueError(
                f"Unrecognized parameters passed to pymatgen converter: {kwargs.keys()}"
            )

        positions = [list(site.position) for site in self.properties.sites]

        try:
            return Structure(
                lattice,
                species,
                positions,
                coords_are_cartesian=True,
                **additional_kwargs,
            )
        except ValueError as err:
            raise ValueError(
                "Singular cell detected. Probably the cell was not set?"
            ) from err

    def _get_object_pymatgen_molecule(self, **kwargs):
        """Converts
        :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
        to pymatgen Molecule object

        :return: a pymatgen Molecule object corresponding to this
          :py:class:`StructureData <aiida.orm.nodes.data.structure.StructureData>`
          object.

        .. note:: Requires the pymatgen module (version >= 3.0.13, usage
            of earlier versions may cause errors)
        """
        from pymatgen.core.structure import Molecule

        if kwargs:
            raise ValueError(
                f"Unrecognized parameters passed to pymatgen converter: {kwargs.keys()}"
            )

        species = []
        additional_kwargs = {}

        for site in self.properties.sites:
            if hasattr(site, "weights"):
                weight = site.weights
            else:
                weight = 1
            species.append({site.symbols: weight})

        positions = [list(site.positions) for site in self.properties.sites]
        mol =  Molecule(species, positions)

        additional_kwargs["site_properties"] = {
                "kinds": self.properties.kind_names,
                "charge": self.properties.charges,
                "magmom": self.properties.magmoms
            }

        for prop,value in additional_kwargs.items():
            mol.add_site_property(prop, value)

    def _get_dimensionality(
        self,
    ):
        """Return the dimensionality of the structure and its length/surface/volume.

        Zero-dimensional structures are assigned "volume" 0.

        :return: returns a dictionary with keys "dim" (dimensionality integer), "label" (dimensionality label)
            and "value" (numerical length/surface/volume).
        """
        import numpy as np

        retdict = {}

        pbc = np.array(self.properties.pbc)
        cell = np.array(self.properties.cell)

        dim = len(pbc[pbc])

        retdict["dim"] = dim
        retdict["label"] = self._dimensionality_label[dim]

        if dim not in (0, 1, 2, 3):
            raise ValueError(f"Dimensionality {dim} must be one of 0, 1, 2, 3")

        if dim == 0:
            # We have no concept of 0d volume. Let's return a value of 0 for a consistent output dictionary
            retdict["value"] = 0
        elif dim == 1:
            retdict["value"] = np.linalg.norm(cell[pbc])
        elif dim == 2:
            vectors = cell[pbc]
            retdict["value"] = np.linalg.norm(np.cross(vectors[0], vectors[1]))
        elif dim == 3:
            from aiida_atomistic.data.structure.utils import calc_cell_volume
            retdict["value"] = calc_cell_volume(cell)

        return retdict

    def _validate_dimensionality(
        self,
    ):
        """Check whether the given pbc and cell vectors are consistent."""
        dim = self._get_dimensionality()

        # 0-d structures put no constraints on the cell
        if dim["dim"] == 0:
            return

        # finite-d structures should have a cell with finite volume
        if dim["value"] == 0:
            raise ValueError(
                f'Structure has periodicity {self.properties.pbc} but {dim["dim"]}-d volume 0.'
            )

        return

    def get_symbols_set(self):
        """Return the set of unique chemical symbols in the structure."""
        return set(self.properties.symbols)

    def __len__(
        self,
    ):
        return len(self.properties.sites)
