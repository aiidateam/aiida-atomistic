from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.models import MutableStructureModel, ImmutableStructureModel
from aiida_atomistic.data.structure.setter_mixin import SetterMixin
from aiida_atomistic.data.structure.getter_mixin import GetterMixin

from aiida_atomistic.data.structure.utils import (
    compress_properties_by_kind,
    rebuild_site_lists_from_kind_lists,
    build_sites_from_expanded_properties,
    sites_from_kinds,
)

class StructureData(Data, GetterMixin):

    _mutable = False

    def __init__(self, validate_kinds=True, sites:list[dict]=None, kinds:list[dict]=None, **kwargs):

        if sites is not None and kinds is not None:
            raise ValueError("You cannot provide both `sites` and `kinds`. Please provide only one of them.")

        if kinds is not None:
            sites = sites_from_kinds(kinds)

        self._properties = ImmutableStructureModel(sites=sites, **kwargs)
        super().__init__()

        if validate_kinds and self.kinds is not None:
            self.validate_kinds()

        attributes = self.properties.model_dump(exclude_unset=True, exclude_none=True, warnings=False)
        if self.properties.kind_names is not None:
            compressed = compress_properties_by_kind(attributes)
            attributes.update(compressed)

        attributes.pop("sites", None)
        attributes.pop("kinds", None)

        for prop, value in attributes.items():
            self.base.attributes.set(prop, value)

    @property
    def properties(self):
        if self.is_stored:
            if "kind_names" in self.base.attributes.all:
                attribute_lists = rebuild_site_lists_from_kind_lists(self.base.attributes.all)
                attributes = build_sites_from_expanded_properties(attribute_lists)
            else:
                attributes = build_sites_from_expanded_properties(self.base.attributes.all)

            properties = ImmutableStructureModel(**attributes)
            return properties
        else:
            return self._properties

    @classmethod
    def from_mutable(cls, mutable_structure, validate_kinds=True):
        if not isinstance(mutable_structure, StructureDataMutable):
            raise ValueError(f"Input structure should be of type StructureDataMutable, not {type(mutable_structure)}")
        return cls(validate_kinds=validate_kinds, **mutable_structure.to_dict(exclude_kinds=True))

    def to_mutable(self,):
        return StructureDataMutable(**self.to_dict())

    def get_value(self):
        return StructureDataMutable(**self.to_dict())

class StructureDataMutable(GetterMixin, SetterMixin):

    _mutable = True

    def __init__(self, validate_kinds=True, sites:list[dict]=None, kinds:list[dict]=None, **kwargs):

        if sites is not None and kinds is not None:
            raise ValueError("You cannot provide both `sites` and `kinds`. Please provide only one of them.")

        if kinds is not None:
            sites = sites_from_kinds(kinds)

        self._properties = MutableStructureModel(sites=sites, **kwargs)
        super().__init__()

    @property
    def properties(self):
        return self._properties
