import os
import time
from pathlib import Path

from src.app.shared_kernel.runtime import PeriodicDaemon


class HeartbeatDaemon(PeriodicDaemon):
    """Proves the process is alive, to the supervisor and to telemetry.

    Every tick it touches ``heartbeat_file`` and logs a line. The file is what
    ``scripts/healthcheck.py`` checks: if the event loop hangs, ticks stop, the
    file goes stale and the container turns unhealthy — a crash-only restart
    policy would never notice. The log line makes the same silence visible in
    the telemetry sink. Keep it running next to your own services.
    """

    name = "heartbeat"

    def __init__(self, heartbeat_file: str, *, interval: float) -> None:
        super().__init__(interval=interval)
        self.heartbeat_file = Path(heartbeat_file)
        self.beats = 0

    async def on_start(self) -> None:
        self.heartbeat_file.parent.mkdir(parents=True, exist_ok=True)

    async def tick(self) -> None:
        now = time.time()
        self.heartbeat_file.touch()
        os.utime(self.heartbeat_file, (now, now))

        self.beats += 1
        self.logger.info("heartbeat #%d", self.beats)

    async def on_stop(self) -> None:
        # A stopped daemon must not read as healthy.
        self.heartbeat_file.unlink(missing_ok=True)
