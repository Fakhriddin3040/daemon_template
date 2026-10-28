import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from src.app.infra.daemons.heartbeat import HeartbeatDaemon

pytestmark = [pytest.mark.unit, pytest.mark.infra]

ROOT = Path(__file__).resolve().parents[3]


class TestHeartbeatDaemon:
    async def test_touches_the_file_each_tick_and_removes_it_on_stop(self, tmp_path):
        path = tmp_path / "nested" / "hb"
        daemon = HeartbeatDaemon(str(path), interval=60)

        await daemon.on_start()
        await daemon.tick()
        assert path.exists()
        first = path.stat().st_mtime

        os.utime(path, (first - 100, first - 100))
        await daemon.tick()
        assert path.stat().st_mtime > first - 1
        assert daemon.beats == 2

        await daemon.on_stop()
        assert not path.exists()


def _healthcheck(path: Path, max_age: float = 90) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "DAEMON_HEARTBEAT_FILE": str(path),
        "DAEMON_HEARTBEAT_MAX_AGE": str(max_age),
    }
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "healthcheck.py")],
        env=env,
        capture_output=True,
        text=True,
    )


class TestHealthcheck:
    def test_fresh_heartbeat_is_healthy(self, tmp_path):
        path = tmp_path / "hb"
        path.touch()
        assert _healthcheck(path).returncode == 0

    def test_stale_heartbeat_is_unhealthy(self, tmp_path):
        path = tmp_path / "hb"
        path.touch()
        old = time.time() - 300
        os.utime(path, (old, old))
        assert _healthcheck(path, max_age=90).returncode == 1

    def test_missing_heartbeat_is_unhealthy(self, tmp_path):
        assert _healthcheck(tmp_path / "missing").returncode == 1
