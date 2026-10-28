import asyncio

import pytest

from src.app.shared_kernel.runtime import (
    EXIT_FAILURE,
    EXIT_OK,
    PeriodicDaemon,
    Service,
    ServiceRunner,
    ServiceState,
)

pytestmark = [pytest.mark.unit, pytest.mark.shared_kernel]


class RecordingService(Service):
    def __init__(self, name: str, log: list[str], *, fail_on: str | None = None):
        super().__init__(name)
        self.log = log
        self.fail_on = fail_on

    async def on_start(self) -> None:
        self.log.append(f"{self.name}:start")
        if self.fail_on == "start":
            raise RuntimeError("start failed")

    async def serve(self) -> None:
        if self.fail_on == "serve":
            raise RuntimeError("serve failed")
        if self.fail_on == "return":
            return
        await self.stop_event.wait()

    async def on_stop(self) -> None:
        self.log.append(f"{self.name}:stop")


def _runner(services, **kwargs) -> ServiceRunner:
    return ServiceRunner(services, handle_signals=False, **kwargs)


async def _stop_soon(runner: ServiceRunner, delay: float = 0.01) -> None:
    await asyncio.sleep(delay)
    runner.request_shutdown()


class TestServiceRunner:
    async def test_clean_shutdown_stops_in_reverse_order(self):
        log: list[str] = []
        a, b = RecordingService("a", log), RecordingService("b", log)
        runner = _runner([a, b])

        code, _ = await asyncio.gather(runner.run_async(), _stop_soon(runner))

        assert code == EXIT_OK
        assert log == ["a:start", "b:start", "b:stop", "a:stop"]
        assert a.state == b.state == ServiceState.STOPPED

    async def test_crashing_service_stops_the_others_and_fails(self):
        log: list[str] = []
        ok = RecordingService("ok", log)
        bad = RecordingService("bad", log, fail_on="serve")

        code = await _runner([ok, bad]).run_async()

        assert code == EXIT_FAILURE
        assert bad.state == ServiceState.FAILED
        assert ok.state == ServiceState.STOPPED

    async def test_service_returning_on_its_own_is_a_failure(self):
        code = await _runner([RecordingService("x", [], fail_on="return")]).run_async()
        assert code == EXIT_FAILURE

    async def test_startup_failure_stops_only_started_services(self):
        log: list[str] = []
        services = [
            RecordingService("a", log),
            RecordingService("b", log, fail_on="start"),
            RecordingService("c", log),
        ]

        code = await _runner(services).run_async()

        assert code == EXIT_FAILURE
        assert "c:start" not in log
        assert log[-2:] == ["b:stop", "a:stop"]

    async def test_hooks_wrap_the_services(self):
        log: list[str] = []

        async def up() -> None:
            log.append("hook:up")

        async def down() -> None:
            log.append("hook:down")

        runner = _runner(
            [RecordingService("a", log)], on_startup=[up], on_shutdown=[down]
        )
        await asyncio.gather(runner.run_async(), _stop_soon(runner))

        assert log == ["hook:up", "a:start", "a:stop", "hook:down"]

    async def test_unresponsive_service_is_cancelled_after_timeout(self):
        class Stubborn(Service):
            async def serve(self) -> None:
                await asyncio.sleep(3600)

        runner = _runner([Stubborn()], stop_timeout=0.05)
        code, _ = await asyncio.gather(runner.run_async(), _stop_soon(runner))

        assert code == EXIT_OK

    def test_duplicate_names_are_rejected(self):
        with pytest.raises(ValueError, match="Duplicate"):
            ServiceRunner([RecordingService("a", []), RecordingService("a", [])])


class TestPeriodicDaemon:
    async def test_ticks_until_stopped(self):
        class Counter(PeriodicDaemon):
            ticks = 0

            async def tick(self) -> None:
                self.ticks += 1
                if self.ticks == 3:
                    self.request_stop()

        daemon = Counter(interval=0.001)
        await daemon.serve()

        assert daemon.ticks == 3

    async def test_failing_tick_backs_off_and_recovers(self):
        class Flaky(PeriodicDaemon):
            backoff_base = 0.001
            calls = 0

            async def tick(self) -> None:
                self.calls += 1
                if self.calls < 3:
                    raise RuntimeError("blip")
                self.request_stop()

        daemon = Flaky(interval=0.001)
        await daemon.serve()

        assert daemon.calls == 3
        assert daemon.consecutive_failures == 0

    async def test_gives_up_after_max_consecutive_failures(self):
        class Broken(PeriodicDaemon):
            backoff_base = 0.001

            async def tick(self) -> None:
                raise RuntimeError("down")

        daemon = Broken(interval=0.001, max_consecutive_failures=2)

        with pytest.raises(RuntimeError, match="down"):
            await daemon.serve()
        assert daemon.consecutive_failures == 2

    def test_backoff_is_capped(self):
        class D(PeriodicDaemon):
            backoff_base = 1.0
            max_backoff = 10.0

            async def tick(self) -> None: ...

        daemon = D()
        daemon.consecutive_failures = 20
        assert daemon.next_backoff() == 10.0

    def test_rejects_non_positive_interval(self):
        class D(PeriodicDaemon):
            async def tick(self) -> None: ...

        with pytest.raises(ValueError):
            D(interval=0)
