from uuid import UUID

from dependency_injector.wiring import Provide, inject

from src.app.shared_kernel.providers.execution_context_provider import (
    ExecutionContextProvider,
)
from src.app.shared_kernel.types.execution_context import ExecutionContext


class ExecutionContextMixin:
    @staticmethod
    @inject
    def get_context(
        provider: ExecutionContextProvider = Provide["core.execution_context_provider"],
    ) -> ExecutionContext | None:
        return provider.get_context()

    def _get_trace_id(self) -> UUID | None:
        ctx = self.get_context()
        return ctx.trace_id if ctx else None
