from typing import Dict, Any

from aiida_atomistic.data.structure.properties.property_utils import PropertyCollector

from aiida_atomistic.data.structure.properties.global.pbc import Pbc
from aiida_atomistic.data.structure.properties.custom import CustomProperty

from aiida import orm

LegacyStructureData = orm.StructureData
    
class StructureData(LegacyStructureData):
    
    """
    Extension of the StructureData class. 
    The main new feature is the possibility to store the properties associated to a given system.
    For example it is possible to store magnetization, hubbard U and V, under the `properties` attribute.
    This attribute is created when the StructureData instance is generated. 
    """
    
    def __init__(
        self, 
        cell=None,
        atomic_positions=None,
        pbc=None,
        ase=None,
        pymatgen=None,
        pymatgen_structure=None,
        pymatgen_molecule=None,
        properties: Dict[str, Dict[str, Any]] = {},
        **kwargs,) -> None:
        """
        The '_property_attribute', has to be stored in self., not in cls. as in the first version of the prototype
        Otherwise we have info in the cls, not in the self.
        :: atomic_positions:: a dictionary with a list of symbols, under the key `symbols`, and a list of positions in Angstrom, under the key `positions`.
        """
        if not isinstance(properties, dict):
            raise ValueError(f"The `properties` input is not of the right type. Expected '{type(dict())}', received '{type(properties)}'.")
        
        super().__init__(
            cell,
            pbc,
            ase,
            pymatgen,
            pymatgen_structure,
            pymatgen_molecule,
            **kwargs,
        )
        
        # Private property attribute
        self._property_attribute = PropertyCollector(parent=self, properties=properties)
        
        # Ensure PBC consistency (wrt backward compatibility);
        self.set_pbc(self.properties.pbc.value)
        
        # Enabling the setting of atoms in the cell:
        if atomic_positions:
            for symbols, positions in zip(atomic_positions["symbols"],atomic_positions["positions"]):
                self.append_atom(symbols=symbols, position=positions)
    
    # Setting the properties attribute as immutable.
    # The only drawback is that the `_properties_attribute` one can still be modified. 
    @property
    def properties(self):
        return self._property_attribute

    @properties.setter
    def properties(self,value):
        raise AttributeError("After the initialization, `properties` is a read-only attribute")
    
        