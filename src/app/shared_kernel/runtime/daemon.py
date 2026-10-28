"""A service that does one thing over and over."""

from __future__ import annotations

import time
from abc import abstractmethod

from src.app.shared_kernel.runtime.service import Service


class PeriodicDaemon(Service):
    """Calls ``tick`` every ``interval`` seconds until stopped.

    * The interval is measured start-to-start, so a slow tick does not push the
      schedule; a tick longer than the interval simply runs the next one at once.
    * A failing tick is logged and retried with exponential backoff (capped at
      ``max_backoff``) instead of killing the process: a database blip should not
      restart the container. Set ``max_consecutive_failures`` to give up after N
      failures in a row and let the runner shut the process down.
    * ``run_immediately=False`` waits one interval before the first tick.
    """

    interval: float = 60.0
    run_immediately: bool = True
    backoff_base: float = 1.0
    max_backoff: float = 300.0
    max_consecutive_failures: int | None = None

    def __init__(
        self,
        name: str | None = None,
        *,
        interval: float | None = None,
        run_immediately: bool | None = None,
        max_consecutive_failures: int | None = None,
    ) -> None:
        super().__init__(name)

        if interval is not None:
            self.interval = interval
        if run_immediately is not None:
            self.run_immediately = run_immediately
        if max_consecutive_failures is not None:
            self.max_consecutive_failures = max_consecutive_failures

        if self.interval <= 0:
            raise ValueError(f"{self.name}: interval must be positive")

        self.consecutive_failures = 0

    @abstractmethod
    async def tick(self) -> None:
        """One iteration of work."""

    def next_backoff(self) -> float:
        return min(
            self.backoff_base * 2 ** (self.consecutive_failures - 1), self.max_backoff
        )

    async def serve(self) -> None:
        if not self.run_immediately and await self.sleep(self.interval):
            return

        while not self.stopping:
            started = time.monotonic()

            try:
                await self.tick()
            except Exception:
                self.consecutive_failures += 1
                self.logger.exception(
                    "%s: tick failed (%d in a row)",
                    self.name,
                    self.consecutive_failures,
                )

                if (
                    self.max_consecutive_failures is not None
                    and self.consecutive_failures >= self.max_consecutive_failures
                ):
                    raise

                if await self.sleep(self.next_backoff()):
                    return
                continue

            self.consecutive_failures = 0
            elapsed = time.monotonic() - started

            if await self.sleep(max(self.interval - elapsed, 0)):
                return
