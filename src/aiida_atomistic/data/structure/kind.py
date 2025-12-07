import typing as t
from pydantic import Field

from aiida_atomistic.data.structure.site import FrozenSite, NumpyArray

class Kind(FrozenSite):
    """This class contains the core information about a given kind of the system.

    """
    _mutable: t.ClassVar[bool] = False

    position: t.Optional[NumpyArray] = Field(min_length=3, max_length=3, default=None)

    # additional wrt FrozenSite:
    positions: t.Optional[NumpyArray] = Field(default=None)
    site_indices: t.Optional[t.List[int]] = Field(default=None)

    @property
    def name(self) -> str:
        """Return the name of the kind. This is an alias of `kind_name`."""
        return self.kind_name

    def __repr__(self) -> str:
        """Return a string representation of the Kind."""
        symbol_str = self.kind_name
        pos_str = f"{self.positions}"
        parts = [f"{symbol_str} @ {pos_str}"]
        indexes = (
            ','.join(str(idx) for idx in self.site_indices)
            if self.site_indices is not None else None
        )
        if indexes:
            parts.append(f"sites=[{indexes}]")

        if self.symbol and self.symbol != self.symbol:
            parts.append(f"kind={self.symbol}")
        if self.is_alloy and self.weight:
            weight_str = '/'.join(f"{w:.2f}" for w in self.weight)
            parts.append(f"weight={weight_str}")
        if self.charge is not None:
            parts.append(f"charge={self.charge:.2f}")
        if self.magnetization is not None:
            parts.append(f"magnetization={self.magnetization:.2f}")
        elif self.magmom is not None:
            magmom_str = f"[{self.magmom[0]:.2f}, {self.magmom[1]:.2f}, {self.magmom[2]:.2f}]"
            parts.append(f"magmom={magmom_str}")

        return f"Kind({', '.join(parts)})"
