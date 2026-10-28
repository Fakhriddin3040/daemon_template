"""Runs a set of services as one process.

    runner = ServiceRunner([MyDaemon(), MyConsumer()], on_shutdown=[dispose_db])
    raise SystemExit(runner.run())

Order of events:

1. ``on_startup`` hooks, in order.
2. ``Service.on_start`` for every service, in order. A failure stops the
   services already started (in reverse) and the process exits non-zero.
3. Every ``Service.serve`` runs concurrently.
4. Shutdown begins on SIGINT/SIGTERM, on any ``serve`` raising, or on any
   ``serve`` returning. Every service is asked to stop; those still running
   after ``stop_timeout`` are cancelled.
5. ``Service.on_stop`` for every started service, in reverse order.
6. ``on_shutdown`` hooks, in reverse order.

Exit code: 0 for a clean stop requested by a signal, 1 when a service failed or
finished on its own.
"""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Awaitable, Callable, Iterable, Sequence

from src.app.shared_kernel.runtime.service import Service, ServiceState

logger = logging.getLogger("runtime.runner")

Hook = Callable[[], Awaitable[None]]

EXIT_OK = 0
EXIT_FAILURE = 1


class ServiceRunner:
    def __init__(
        self,
        services: Sequence[Service],
        *,
        on_startup: Iterable[Hook] = (),
        on_shutdown: Iterable[Hook] = (),
        stop_timeout: float = 30.0,
        handle_signals: bool = True,
    ) -> None:
        names = [s.name for s in services]
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            raise ValueError(f"Duplicate service names: {sorted(duplicates)}")

        self.services = list(services)
        self.on_startup = list(on_startup)
        self.on_shutdown = list(on_shutdown)
        self.stop_timeout = stop_timeout
        self.handle_signals = handle_signals

        self._shutdown = asyncio.Event()
        self._failed = False

    # ===== Public =====

    def run(self) -> int:
        """Blocking entrypoint. Returns the process exit code."""
        try:
            return asyncio.run(self.run_async())
        except KeyboardInterrupt:
            # Only reachable when signal handlers could not be installed.
            return EXIT_OK

    async def run_async(self) -> int:
        if not self.services:
            logger.warning("runner: no services registered, nothing to run")
            return EXIT_OK

        if self.handle_signals:
            self._install_signal_handlers()

        started: list[Service] = []

        try:
            for hook in self.on_startup:
                await hook()

            for service in self.services:
                service.state = ServiceState.STARTING
                started.append(service)
                await service.on_start()
                logger.info("runner: started %s", service.name)

            await self._serve_all(started)
        except Exception:
            self._failed = True
            logger.exception("runner: startup failed")
        finally:
            await self._stop_all(started)
            await self._run_shutdown_hooks()

        return EXIT_FAILURE if self._failed else EXIT_OK

    def request_shutdown(self) -> None:
        if not self._shutdown.is_set():
            logger.info("runner: shutdown requested")
        self._shutdown.set()

    # ===== Internals =====

    def _install_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self.request_shutdown)
            except NotImplementedError:  # pragma: no cover - windows
                pass

    async def _serve_all(self, services: list[Service]) -> None:
        tasks = {
            asyncio.create_task(self._serve_one(s), name=f"service:{s.name}"): s
            for s in services
        }
        shutdown_wait = asyncio.create_task(self._shutdown.wait())

        try:
            # Wake up on the first service to finish *or* a shutdown request.
            await asyncio.wait(
                [*tasks, shutdown_wait], return_when=asyncio.FIRST_COMPLETED
            )
        finally:
            shutdown_wait.cancel()

        for service in services:
            service.request_stop()

        pending = [t for t in tasks if not t.done()]
        if pending:
            _, still_running = await asyncio.wait(pending, timeout=self.stop_timeout)
            for task in still_running:
                logger.warning(
                    "runner: %s did not stop within %.1fs, cancelling",
                    tasks[task].name,
                    self.stop_timeout,
                )
                task.cancel()
            await asyncio.gather(*still_running, return_exceptions=True)

    async def _serve_one(self, service: Service) -> None:
        service.state = ServiceState.RUNNING

        try:
            await service.serve()
        except asyncio.CancelledError:
            raise
        except Exception:
            service.state = ServiceState.FAILED
            self._failed = True
            logger.exception("runner: %s crashed", service.name)
            self.request_shutdown()
            return

        if not service.stopping:
            # `serve` returned without being asked to: treat as a failure so the
            # supervisor (docker, systemd) restarts the process.
            self._failed = True
            logger.error("runner: %s exited on its own", service.name)
            self.request_shutdown()

    async def _stop_all(self, services: list[Service]) -> None:
        for service in reversed(services):
            if service.state != ServiceState.FAILED:
                service.state = ServiceState.STOPPING
            try:
                await service.on_stop()
            except Exception:
                self._failed = True
                logger.exception("runner: %s failed to stop cleanly", service.name)
            if service.state != ServiceState.FAILED:
                service.state = ServiceState.STOPPED
            logger.info("runner: stopped %s", service.name)

    async def _run_shutdown_hooks(self) -> None:
        for hook in reversed(self.on_shutdown):
            try:
                await hook()
            except Exception:
                self._failed = True
                logger.exception("runner: shutdown hook %r failed", hook)
