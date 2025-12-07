from aiida.orm.nodes.data import Data

from aiida_atomistic.data.structure.models import MutableStructureModel, ImmutableStructureModel
from aiida_atomistic.data.structure.setter_mixin import SetterMixin
from aiida_atomistic.data.structure.getter_mixin import GetterMixin

import warnings

class StructureData(Data, GetterMixin):

    _mutable = False
    _model = ImmutableStructureModel

    def __init__(self, sites:list[dict]=None, kinds:list[dict]=None, **kwargs):

        from aiida_atomistic.data.structure.utils_kinds import sites_from_kinds

        if sites is not None and kinds is not None:
            warnings.warn("Provided both `sites` and `kinds` information. Dropping the `sites` information and using only `kinds`.")
            sites = sites_from_kinds(kinds)
        elif kinds is not None:
            sites = sites_from_kinds(kinds)

        self._properties = self._model(sites=sites, **kwargs)
        super().__init__()

        #if validate_kinds:
        #    if self.kinds is not None: self.validate_kinds()

        attributes = self.properties.model_dump(exclude_unset=True, exclude_none=True, warnings=False)
        if self.properties.kind_names is not None:
            from aiida_atomistic.data.structure.utils_kinds import compress_properties_by_kind
            compressed = compress_properties_by_kind(attributes)
            attributes.update(compressed)

        attributes.pop("sites", None)
        attributes.pop("kinds", None)

        for prop, value in attributes.items():
            self.base.attributes.set(prop, value)

    @property
    def properties(self):
        if self.is_stored:
            from aiida_atomistic.data.structure.utils import build_sites_from_expanded_properties
            if "kind_names" in self.base.attributes.all:
                from aiida_atomistic.data.structure.utils_kinds import rebuild_site_lists_from_kind_lists
                attribute_lists = rebuild_site_lists_from_kind_lists(self.base.attributes.all)
                attributes = build_sites_from_expanded_properties(attribute_lists)
            else:
                attributes = build_sites_from_expanded_properties(self.base.attributes.all)

            properties = self._model(**attributes)
            return properties
        else:
            return self._properties

    @classmethod
    def from_builder(cls, builder: 'StructureBuilder'):
        from aiida_atomistic.data.structure.structure import StructureBuilder
        if not isinstance(builder, StructureBuilder):
            raise ValueError(f"Input builder should be of type StructureBuilder, not {type(builder)}")
        return cls(**builder.to_dict())

    def to_builder(self) -> 'StructureBuilder':
        return StructureBuilder(**self.to_dict())

    def __repr__(self) -> str:
        """Return a concise string representation of the structure."""

        from aiida_atomistic.data.structure.utils import build_concise_structure_repr

        # Build UUID string without calling super().__repr__() to avoid recursion
        if self.is_stored:
            uuid_str = f'<{self.__class__.__name__}: uuid: {self.uuid} (pk: {self.pk})>'
        else:
            uuid_str = f'<{self.__class__.__name__}: uuid: {self.uuid} (unstored)>'

        prop_repr_str = build_concise_structure_repr(self)
        return uuid_str + f'\n {prop_repr_str.replace("ImmutableStructureModel","")}'

    def __str__(self) -> str:
        """Return a string representation of the structure for print()."""
        return self.__repr__()

class StructureBuilder(GetterMixin, SetterMixin):

    _mutable = True
    _model = MutableStructureModel

    def __init__(self, sites:list[dict]=None, kinds:list[dict]=None, **kwargs):

        from aiida_atomistic.data.structure.utils_kinds import sites_from_kinds

        if sites is not None and kinds is not None:
            warnings.warn("Provided both `sites` and `kinds` information. Dropping the `sites` information and using only `kinds`.")
            sites = sites_from_kinds(kinds)
        elif kinds is not None:
            sites = sites_from_kinds(kinds)

        self._properties = self._model(sites=sites, **kwargs)
        super().__init__()

    @property
    def properties(self):
        return self._properties

    @classmethod
    def from_aiida(cls, aiida: 'StructureData'):
        if not isinstance(aiida, StructureBuilder):
            raise ValueError(f"Input aiida should be of type StructureBuilder, not {type(aiida)}")
        return cls(**aiida.to_dict())

    def to_aiida(self) -> 'StructureData':
        return StructureData(**self.to_dict())

    def __repr__(self) -> str:
        """Return a concise string representation of the structure."""

        from aiida_atomistic.data.structure.utils import build_concise_structure_repr

        prop_repr_str = build_concise_structure_repr(self)
        return super().__repr__() + f'\n {prop_repr_str.replace("MutableStructureModel","")}'

    def __str__(self) -> str:
        """Return a string representation of the structure for print()."""
        return self.__repr__()
