"""Mapper-level listeners that stamp audit columns.

Doing it here rather than in every repository means a new model gets
`created_at` / `updated_at` for free the moment it inherits `ChronoModelMixin`.
"""

from dependency_injector.wiring import Provide, inject
from sqlalchemy import event

from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.shared_kernel.ports.services import ClockProto


@event.listens_for(SqlAlchemyBaseModel, "before_insert", propagate=True)
@inject
def set_created_props(
    mapper,
    connection,
    target,
    clock: ClockProto = Provide["core.services.clock"],
) -> None:
    if hasattr(target, "created_at"):
        target.created_at = clock.get_now()


@event.listens_for(SqlAlchemyBaseModel, "before_update", propagate=True)
@inject
def set_updated_props(
    mapper,
    connection,
    target,
    clock: ClockProto = Provide["core.services.clock"],
) -> None:
    if hasattr(target, "updated_at"):
        target.updated_at = clock.get_now()
