from contextvars import ContextVar, Token
from typing import Tuple

from src.app.shared_kernel.types.execution_context import ExecutionContext


class ExecutionContextProvider:
    _registry: ContextVar[ExecutionContext] = ContextVar("execution_context")

    @classmethod
    def create(cls, **payload) -> Tuple[ExecutionContext, Token]:
        ctx = ExecutionContext(payload=payload)
        token = cls._registry.set(ctx)
        return ctx, token

    @classmethod
    def get_context(cls) -> ExecutionContext | None:
        return cls._registry.get(None)

    @classmethod
    def clear(cls, token: Token) -> None:
        cls._registry.reset(token)
