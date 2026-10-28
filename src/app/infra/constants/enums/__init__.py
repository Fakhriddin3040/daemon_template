import enum


class AggregateName(enum.StrEnum):
    """Every aggregate that raises domain events. Add one per aggregate in ``core``."""
