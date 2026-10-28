from typing import Any, Dict
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ExecutionContext(BaseModel):
    """Per-unit-of-work context: one request, one job, one daemon tick.

    ``payload`` is deliberately untyped — what a unit of work needs to carry
    (an actor, a tenant, a source) is the application's business, not the
    template's.
    """

    trace_id: UUID = Field(default_factory=uuid4)
    payload: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)
