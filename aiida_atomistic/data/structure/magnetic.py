import copy
import functools
import itertools
import json
import typing
from typing import List
from pydantic import BaseModel, Field
from abc import ABCMeta

from aiida_atomistic.data.structure.property import * 

class Magnetization(BaseProperty):
    value: List[float] = Field(default=None)
    
    ## here goes some validator against some property of the structure, e.g. number of sites, kinds...