# -*- coding: utf-8 -*-
"""Utility class for handling the :class:`aiida_atomistic.data.structure.structure.StructureData` if
magnetization property is set and used in the aiida-quantumespresso plugin."""
# pylint: disable=no-name-in-module
from itertools import product
import os
from typing import List, Tuple, Union

from aiida.plugins import DataFactory

StructureData = DataFactory("atomistic.structure")

class MagneticUtils:
    """Utility class for handling `Magnetization` properties for QuantumESPRESSO.
       At the moment we support only kind-based collinear magnetization.
    """

    def __init__(
        self,
        structure: StructureData,
    ):
        """Set a the `StructureData` to manipulate."""
        if isinstance(structure, StructureData):
            self.structure = structure
        else:
            raise ValueError('input is not of type `StructureData')
        
    def get_magnetic_card(self, collinear=True):
        magnetization = self.structure.get_property_attribute("magnetization")
        collinear_kind_moments= magnetization["collinear_kind_moments"]
        
        return collinear_kind_moments