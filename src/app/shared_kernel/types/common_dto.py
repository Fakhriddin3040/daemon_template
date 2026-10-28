import msgspec

from src.app.shared_kernel.types.base_types import ID_T


class NameDTO(msgspec.Struct):
    """Universal dto for storing only `name`"""

    name: str


class NameIdDTO(msgspec.Struct):
    """Universal dto for storing only `id` and `name`"""

    id: ID_T
    name: str


class TitleIdDTO(msgspec.Struct):
    """Universal dto for storing only `id` and `title`"""

    id: ID_T
    title: str
