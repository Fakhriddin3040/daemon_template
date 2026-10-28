"""The unit a process is built from.

A ``Service`` is anything with a lifetime: a daemon loop, a queue consumer, a
custom socket server. The ``ServiceRunner`` drives every service through the
same three phases, so a process made of several services starts, runs and stops
as one.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import StrEnum


class ServiceState(StrEnum):
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class Service(ABC):
    """Base for a long-running unit of work.

    Lifecycle, as driven by ``ServiceRunner``:

    1. ``on_start`` — acquire resources. Runs before *any* service serves, so a
       failure here aborts the whole process before it does work.
    2. ``serve`` — the body. Runs until it returns, raises, or ``stop_event`` is
       set. Returning normally means "done": the runner then shuts the process
       down, because a service that silently finished is almost always a bug.
    3. ``on_stop`` — release resources. Always runs for a started service,
       including after ``serve`` raised.

    ``serve`` should watch ``self.stop_event`` (or ``self.sleep``) rather than be
    cancelled: a cooperative stop lets the current iteration finish cleanly.
    Cancellation is the fallback once the runner's stop timeout runs out.
    """

    name: str = ""

    def __init__(self, name: str | None = None) -> None:
        self.name = name or self.name or type(self).__name__
        self.state = ServiceState.CREATED
        self.stop_event = asyncio.Event()
        self.logger = logging.getLogger(f"service.{self.name}")

    async def on_start(self) -> None:  # noqa: B027  (optional hook)
        """Acquire resources. Override when needed."""

    @abstractmethod
    async def serve(self) -> None:
        """The service body."""

    async def on_stop(self) -> None:  # noqa: B027  (optional hook)
        """Release resources. Override when needed."""

    def request_stop(self) -> None:
        """Ask ``serve`` to finish. Idempotent and safe from a signal handler."""
        self.stop_event.set()

    @property
    def stopping(self) -> bool:
        return self.stop_event.is_set()

    async def sleep(self, seconds: float) -> bool:
        """Sleep that wakes up early on stop.

        Returns ``True`` when the stop was requested, so a loop reads as
        ``if await self.sleep(5): break``.
        """
        try:
            await asyncio.wait_for(self.stop_event.wait(), timeout=seconds)
        except TimeoutError:
            return False
        return True

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r} state={self.state}>"
