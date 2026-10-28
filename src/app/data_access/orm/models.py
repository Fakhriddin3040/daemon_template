"""Single import surface for every ORM model.

Alembic's autogenerate and SQLAlchemy's mapper configuration both need every
model imported before they run; doing it here means one import instead of a list
that silently goes stale. Add each new model to this module.
"""

from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.data_access.orm.telemetry.models.log_record_orm_model import (
    LogRecordOrmModel,
    LogRecordTracebackOrmModel,
)

__all__ = [
    "SqlAlchemyBaseModel",
    "LogRecordOrmModel",
    "LogRecordTracebackOrmModel",
]
