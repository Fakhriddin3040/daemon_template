"""Scopes a daemon tick or a job runs inside.

An HTTP app opens a session per request in middleware; a daemon has no request,
so it opens one per unit of work instead:

    async def tick(self) -> None:
        async with unit_of_work_scope(source=self.name) as uow:
            ...  # repositories resolve `db.session` to this scope's session
            # commit on clean exit, rollback on exception
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from src.app.infra.globals import DIContainerRegistry
from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.providers.execution_context_provider import (
    ExecutionContextProvider,
)


@asynccontextmanager
async def unit_of_work_scope(**payload) -> AsyncIterator[UnitOfWorkProto]:
    """A fresh execution context + DB session + unit of work.

    ``payload`` lands on ``ExecutionContext.payload``.
    """
    root = DIContainerRegistry.get_root_container()
    _, ctx_token = ExecutionContextProvider.create(**payload)
    session_token = root.db.set_current_session()

    try:
        async with root.db.uow() as uow:
            yield uow
    finally:
        await root.db.clear_current_session(session_token)
        ExecutionContextProvider.clear(ctx_token)
