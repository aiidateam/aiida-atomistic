from typing import List, Literal, Tuple, Dict
from aiida_muon.workflows.utils import get_collinear_mag_kindname
from pymatgen.electronic_structure.core import Magmom
from pydantic import Field
import numpy

from aiida_atomistic.data.structure.properties.property import * 

class Magnetization(BaseProperty):
    moments: List[Tuple[float,float,float]] = Field(default=None) #should be validated against the number of sites.
    collinear_kind_moments: Dict[str,float] = Field(default=None)
    units: Literal["Bohr_magneton"] = "Bohr_magneton"
    
       
    def set_from_components(
        self,
        magnetic_moment_per_site: List[float] = None,
        magnetic_moment_per_kind: Dict[str,float] = None, 
        coordinates: Literal["cartesian","spherical","collinear"] = "cartesian", 
        use_kinds: bool = True, 
        atol: float = 0.5, 
        ztol: float = 0.49,
        ):
        """Create a new magnetic configuration from the given structure based on a list of magnetic moments per site.
        Updates 
            -   the structure.magnetization property and provides both 
                moments and collinear_kind_moments (if kind_base=True. 
                This is a dict kind->magn, magn being a float).
            -   the kinds, if kind_base=True.

        :param structure: a `StructureData` instance.
        :param magnetic_moment_per_site: list of magnetic moments for each site in the structure. Can be both 3D arrays or floats (collinear).
        :param atol: the absolute tolerance on determining if two sites have the same magnetic moment.
        :param ztol: threshold for considering a kind to have non-zero magnetic moment.
        
        """
        
        if not magnetic_moment_per_site and not magnetic_moment_per_kind:
            raise ValueError('You have to provide one among "magnetic_moment_per_site" and "magnetic_moment_per_kind"')
        if magnetic_moment_per_site and magnetic_moment_per_kind:
            raise ValueError('You have to provide only one among "magnetic_moment_per_site" and "magnetic_moment_per_kind"')
        
        moments = []
        collinear_kind_moments = []
        
        if magnetic_moment_per_kind:
            magnetic_moment_per_site = []
            coordinates = "collinear" #for now we support only collinear, i.e. list of floats.
            for site in self.parent.sites:
                if site.kind_name in magnetic_moment_per_kind:
                    magnetic_moment_per_site.append(magnetic_moment_per_kind[site.kind_name])
                else:
                    magnetic_moment_per_site.append(0.0)
        
        
        #consistency check
        if len(magnetic_moment_per_site)!=len(self.parent.sites):
            raise ValueError("The number of magnetic moments does not match with the number of sites in the structure.")
        
        #translate moments to 3D cartesian coordinates, if needed
        moments = transform_moments(moments=magnetic_moment_per_site,initial=coordinates, final="cartesian")
            
        #collinear pro kinds:
        collinear_kind_moments = make_collinear_getmag_kind(self.parent,magnetic_moment_per_site,coordinates,half=False,atol=atol,ztol=ztol)
        
        return self.parent.set_property(pname="magnetization",pvalue={'moments':moments,'collinear_kind_moments':collinear_kind_moments})

def transform_moments(moments,initial,final):
    """Translate moments from one system to another.
    """
    if initial == final: return moments
    else:
        new_moments = []
        if [initial,final] == ["collinear","cartesian"]:
            for m in moments:
                new_moments.append([0,0,m])
        else:
            raise NotImplementedError(f"Transformation from {initial} to {final} coordinates is not yet implemented")
        return new_moments


def create_magnetic_configuration(
    structure, 
    magnetic_moment_per_site, 
    atol: float = 0.5, 
    ztol: float = 0.49,
):
    """Create a new magnetic configuration from the given structure based on a list of magnetic moments per site.

    To create the new list of kinds, the algorithm loops over all the elements in the structure and makes a list of the
    sites with that element and their corresponding magnetic moment. Next, it splits this list in three lists:

    * Zero magnetic moments: Any site that has an absolute magnetic moment lower than ``ztol``
    * Positive magnetic moments
    * Negative magnetic moments

    The algorithm then sorts the positive and negative lists from large to small absolute value, and loops over each of
    list. New magnetic kinds will be created when the absolute difference between the magnetic moment of the current
    kind and the site exceeds ``atol``.

    The positive and negative magnetic moments are handled separately to avoid assigning two sites with opposite signs
    in their magnetic moment to the same kind and make sure that each kind has the correct magnetic moment, i.e. the
    largest magnetic moment in absolute value of the sites corresponding to that kind.

    .. important:: the function currently does not support alloys.

    :param structure: a `StructureData` instance.
    :param magnetic_moment_per_site: list of magnetic moments for each site in the structure.
    :param atol: the absolute tolerance on determining if two sites have the same magnetic moment.
    :param ztol: threshold for considering a kind to have non-zero magnetic moment.
    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    import string

    if structure.is_alloy:
        raise ValueError('Alloys are currently not supported.')

    rtol = 0  # Relative tolerance used in the ``numpy.is_close()`` calls.

    magnetic_configuration = {}
    
    symbols_set = structure.get_symbols_set()
    sites_ = structure.sites
    
    """
    Before, the clear sites and kinds was done inside the loop, but does not work.
    """
    structure.clear_sites()
    structure.clear_kinds()

    for element in symbols_set:

        # Filter the sites and magnetic moments on the site element
        element_sites, element_magnetic_moments = zip(
            *[(site, magnetic_moment)
              for site, magnetic_moment in zip(sites_, magnetic_moment_per_site)
              if site.kind_name.rstrip(string.digits) == element]
        )

        # Split the sites and their magnetic moments by sign to filter out the sites with magnetic moment lower than
        # `ztol`and deal with the positive and negative magnetic moment separately. This is important to avoid assigning
        # two sites with opposite signs to the same kind and make sure that each kind has the correct magnetic moment,
        # i.e. the largest magnetic moment in absolute value of the sites corresponding to that kind.
        zero_sites = []
        pos_sites = []
        neg_sites = []

        for site, magnetic_moment in zip(element_sites, element_magnetic_moments):

            if abs(magnetic_moment) <= ztol:
                zero_sites.append((site, 0))
            elif magnetic_moment > 0:
                pos_sites.append((site, magnetic_moment))
            else:
                neg_sites.append((site, magnetic_moment))

        kind_index = -1
        kind_names = []
        kind_sites = []
        kind_magnetic_moments = {}

        for site_list in (zero_sites, pos_sites, neg_sites):

            if not site_list:
                continue

            # Sort the site list in order to build the kind lists from large to small absolute magnetic moment.
            site_list = sorted(site_list, key=lambda x: abs(x[1]), reverse=True)

            sites, magnetic_moments = zip(*site_list)

            kind_index += 1
            current_kind_name = f'{element}{kind_index}'
            kind_sites.append(sites[0])
            kind_names.append(current_kind_name)
            kind_magnetic_moments[current_kind_name] = magnetic_moments[0]

            for site, magnetic_moment in zip(sites[1:], magnetic_moments[1:]):

                if not numpy.isclose(magnetic_moment, kind_magnetic_moments[current_kind_name], rtol, atol):
                    kind_index += 1
                    current_kind_name = f'{element}{kind_index}'
                    kind_magnetic_moments[current_kind_name] = magnetic_moment

                kind_sites.append(site)
                kind_names.append(current_kind_name)

        # In case there is only a single kind for the element, remove the 0 kind index
        if current_kind_name == f'{element}0':
            kind_names = len(element_magnetic_moments) * [element]
            kind_magnetic_moments = {element: kind_magnetic_moments[current_kind_name]}

        magnetic_configuration.update(kind_magnetic_moments)


        for name, site in zip(kind_names, kind_sites):
            structure.append_atom(
                name=name,
                symbols=(element,),
                weights=(1.0,),
                position=site.position,
            )

    return magnetic_configuration

def make_collinear_getmag_kind(
    structure,
    magnetic_moment_per_site: List[float], 
    coordinates: Literal["cartesian", "spherical","collinear"] = "cartesian", 
    half=False, 
    atol: float = 0.5, 
    ztol: float = 0.49
    ):
    """
    This calls the 'get_collinear_mag_kindname' utility function.
    It takes the provided magnetic, make it collinear and then with
    assign kind_name property for each atom site relevant
    spin polarized calculation.

    Returns: Structure data and dictionary of pw starting magnetization card.
    """
    magmom_list = []
    if coordinates!="collinear":
        p_st = structure.get_pymatgen_structure()
        # magmm = magnetic_node.get_array('magnetic')
        # from array to magnetic object
        magnetics = [Magmom(magnetic) for magnetic in magnetic_moment_per_site]
        
        st_k, st_m_dict = get_collinear_mag_kindname(p_st, magnetics, half)

        magmom_list = []
        for sites in st_k.site_properties['kind_name']:
            if not sites: #None, so no magnetization
                magmom_list.append(0)
            else:
                magmom_list.append(st_m_dict[sites])
            
        structure.clear_sites()
        structure.clear_kinds()
        for name, site in zip(st_k.site_properties['kind_name'], st_k.sites):
            if not name: #None, so no magnetization
                kind = site.species_string
            else:
                kind = name
            structure.append_atom(
                name=kind,
                symbols=(site.species_string,),
                weights=(1.0,),
                position=site.coords,
            )   
    else:
        magmom_list = magnetic_moment_per_site
        
           
    #this is done in order to have the correct structure with kinds and the magnetization card 
    #after the first collinearization of "get_collinear_mag_kindname"
    st_m_dict = create_magnetic_configuration(structure,magmom_list,atol,ztol)

    magmom_list = []
    for site in structure.sites:
        magmom_list.append(st_m_dict[site.kind_name])
    
    
    print(f"Setting magnetization to {st_m_dict}")
    
    return st_m_dict