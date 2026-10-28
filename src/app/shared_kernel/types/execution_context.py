from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.app.shared_kernel.utils.functions.uuid_funcs import uuid7


class ExecutionContext(BaseModel):
    """Per-unit-of-work context: one request, one job, one daemon tick.

    ``payload`` is deliberately untyped — what a unit of work needs to carry
    (an actor, a tenant, a source) is the application's business, not the
    template's.
    """

    trace_id: UUID = Field(default_factory=uuid7)
    payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)
