from src.app.shared_kernel.runtime import PeriodicDaemon


class HeartbeatDaemon(PeriodicDaemon):
    """Logs that the process is alive.

    The default service so a fresh clone has something to run; replace it with
    real services in `main.py`. The log line also reaches the telemetry sink,
    which makes a silent process visible there.
    """

    name = "heartbeat"
    interval = 60.0

    async def tick(self) -> None:
        self.logger.info("heartbeat")
