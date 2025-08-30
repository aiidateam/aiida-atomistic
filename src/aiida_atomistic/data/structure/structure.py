from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.models import MutableStructureModel, ImmutableStructureModel
from aiida_atomistic.data.structure.setter_mixin import SetterMixin
from aiida_atomistic.data.structure.getter_mixin import GetterMixin

class StructureData(Data, GetterMixin):

    _mutable = False

    def __init__(self, **kwargs):

        self._properties = ImmutableStructureModel(**kwargs)
        super().__init__()

        defined_properties = self.get_defined_properties().union(self.properties.model_computed_fields.keys()).difference({"sites"}) # exclude the default ones. We do not need to store them into the db.
        for prop, value in self.properties.model_dump(exclude_defaults=True).items():
            if prop in defined_properties:
                self.base.attributes.set(prop, value)

    @property
    def properties(self):
        if self.is_stored:
            return ImmutableStructureModel(**self.base.attributes.all)
        else:
            return self._properties

    @classmethod
    def from_mutable(cls, mutable_structure, detect_kinds: bool = False):
        if not isinstance(mutable_structure, StructureDataMutable):
            raise ValueError(f"Input structure should be of type StructureDataMutable, not {type(mutable_structure)}")
        return cls(**mutable_structure.to_dict(detect_kinds=detect_kinds))

    def get_value(self, detect_kinds: bool = False):
        return StructureDataMutable(**self.to_dict(detect_kinds=detect_kinds))

class StructureDataMutable(GetterMixin, SetterMixin):

    _mutable = True

    def __init__(self, **kwargs):

        self._properties = MutableStructureModel(**kwargs)

    @property
    def properties(self):
        return self._properties
