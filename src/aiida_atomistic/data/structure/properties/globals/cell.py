from typing import List
from pydantic import Field

from aiida_atomistic.data.structure.properties.property_utils import BaseProperty

################################################## Start: Cell property:

class Cell(BaseProperty):
    """
    The cell property. 
    It is different from the cell attribute directly accessible from the StructureData object.
    """
    domain = "global"
    value: List[List[float]] = Field(default=None, min_items=3,max_items=3)

    def get_cell_volume(self):
        """
        Compute the three-dimensional cell volume in Angstrom^3.

        :returns: the cell volume.
        """
        import numpy as np
        return np.abs(np.dot(self.value[0], np.cross(self.value[1], self.value[2])))

################################################## End: Cell property.