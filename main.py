"""Daemon entrypoint: `python main.py`.

Builds the DI graph, then runs every registered service under one
`ServiceRunner` until SIGINT/SIGTERM. Register your services in
`build_services`.
"""

from src.app.infra.daemons.heartbeat import HeartbeatDaemon
from src.app.modules.telemetry.logging import install_root_handler
from src.app.shared_kernel.config.infra_configs import DaemonConfig
from src.app.shared_kernel.runtime import Service, ServiceRunner
from src.bootstrap import Bootstrap


def build_services(config: DaemonConfig) -> list[Service]:
    return [
        # Keep it: it is what the container healthcheck watches.
        HeartbeatDaemon(config.heartbeat_file, interval=config.heartbeat_interval),
        # Your services go here.
    ]


def main() -> int:
    root = Bootstrap.init_di_containers()
    config = root.config.daemon()

    # Plain `logging` calls in this process land in the telemetry file sink the
    # telemetry daemon tails.
    install_root_handler("daemon")

    runner = ServiceRunner(
        build_services(config),
        on_startup=[Bootstrap.bootstrap_async],
        on_shutdown=[Bootstrap.shutdown_async],
        stop_timeout=config.stop_timeout,
    )
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
