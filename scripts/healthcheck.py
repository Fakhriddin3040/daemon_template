"""Liveness probe: exit 0 while the heartbeat file is fresh, 1 otherwise.

    python3 scripts/healthcheck.py

Used by the compose healthcheck. Reads the same `DAEMON_*` settings as the
daemon, so the two can never disagree about where the file is.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app.shared_kernel.config.infra_configs import DaemonConfig  # noqa: E402


def main() -> int:
    config = DaemonConfig()
    path = Path(config.heartbeat_file)

    try:
        age = time.time() - path.stat().st_mtime
    except FileNotFoundError:
        print(f"unhealthy: {path} does not exist")
        return 1

    if age > config.heartbeat_max_age:
        print(f"unhealthy: last heartbeat {age:.0f}s ago (max {config.heartbeat_max_age:.0f}s)")
        return 1

    print(f"healthy: last heartbeat {age:.0f}s ago")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
