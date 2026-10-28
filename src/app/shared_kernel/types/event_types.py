import time
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field

from src.app.shared_kernel.data_structures.mappings import NamedDict
from src.app.shared_kernel.pydantic.types import BasePydanticModel


class EventMeta(NamedDict):
    """
    BaseEvent metadata model.
    For storing dynamic data for event.
    """


class BaseEvent(BasePydanticModel):
    """
    BaseEvent representation model
    """

    event_id: UUID = Field(default_factory=uuid4)
    occurred_on: float = Field(init=False, default_factory=time.time)
    order: int = 0
    meta: Optional[EventMeta] = None
