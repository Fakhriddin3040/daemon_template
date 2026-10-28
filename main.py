"""Application entrypoint: `python main.py`.

Builds the DI graph, then runs every registered service under one
`ServiceRunner` until SIGINT/SIGTERM. Register your services in
`build_services`.
"""

from src.app.infra.daemons.heartbeat import HeartbeatDaemon
from src.app.modules.telemetry.logging import install_root_handler
from src.app.shared_kernel.runtime import Service, ServiceRunner
from src.bootstrap import Bootstrap


def build_services() -> list[Service]:
    return [
        HeartbeatDaemon(),
    ]


def main() -> int:
    Bootstrap.init_di_containers()

    # Plain `logging` calls in this process land in the telemetry file sink the
    # daemon tails.
    install_root_handler("app")

    runner = ServiceRunner(
        build_services(),
        on_startup=[Bootstrap.bootstrap_async],
        on_shutdown=[Bootstrap.shutdown_async],
    )
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
