"""Which ORM model backs which domain entity.

The entity-source factory reads this both ways: domain -> ORM when building a
new aggregate, and ORM -> domain when hydrating one from a loaded row. Register
each aggregate from ``core`` here, e.g. ``{OrderAggregate: OrderOrmModel}``.
"""

from typing import Dict, Type

from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel

ENTITY_ORM_MODEL_MAP: Dict[type, Type[SqlAlchemyBaseModel]] = {}
