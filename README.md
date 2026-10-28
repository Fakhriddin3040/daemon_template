# daemon_template

A base project for a Python **daemon** to clone: a worker, a scheduler, a
bot, a consumer, anything long-running that isn't an HTTP API. A supervised
service runner, a liveness probe, the database, cache, DI and telemetry are
already wired. There are no
models, no users and no API, so you start with your own `core` and none of
someone else's.

**Stack:** SQLAlchemy 2 (async) · PostgreSQL · Redis · Alembic ·
`dependency-injector` · pydantic / msgspec.

---

## Quick start

```bash
git clone <this> my-daemon && cd my-daemon
cp .env.example .env
python scripts/utils/generate_secret.py   # paste the two secrets into .env

# pick one
uv sync --group dev
poetry install --with dev
pip install -r requirements/dev.txt

alembic upgrade head
python main.py          # Ctrl+C to stop
```

Out of the box `main.py` runs a `HeartbeatDaemon`, which keeps the liveness
file fresh and logs every `DAEMON_HEARTBEAT_INTERVAL` seconds. Add your own
services next to it in `build_services()`.

Or with Docker (daemon + db + redis + telemetry):

```bash
docker compose up --build
```

---

## Layout

```
main.py                       entrypoint: DI + ServiceRunner
scripts/healthcheck.py        liveness probe (compose healthcheck)
runner.py                     telemetry daemon entrypoint
src/
├── bootstrap.py              DI wiring, async startup, shutdown
└── app/
    ├── core/                 YOUR domain: empty on purpose
    ├── data_access/          ORM base, base repository, UoW, entity sources
    ├── infra/                DI containers, services, runtime scopes, daemons
    ├── modules/              self-contained, liftable subsystems
    │   ├── telemetry/        structured logging → Postgres + Telegram
    │   └── cache/            Redis client + key building
    └── shared_kernel/        types, configs, Result, errors, runtime
        └── runtime/          Service, PeriodicDaemon, ServiceRunner
```

- **`core/` holds domain only:** entities, aggregates, domain events, params.
  It imports from `shared_kernel`, never from `infra` or `data_access`.
- **`modules/` is for subsystems with no knowledge of the domain.** They can be
  copied into another project as they are.

---

## Runtime

A process is a list of `Service`s run by one `ServiceRunner`.

```python
from src.app.infra.runtime.scopes import unit_of_work_scope
from src.app.shared_kernel.runtime import PeriodicDaemon


class ExpireOrdersDaemon(PeriodicDaemon):
    name = "expire-orders"
    interval = 30.0

    async def tick(self) -> None:
        async with unit_of_work_scope(source=self.name) as uow:
            ...  # commit on clean exit, rollback on exception
```

**`Service`** has three phases: `on_start` → `serve` → `on_stop`. `serve`
should watch `self.stop_event` (or use `await self.sleep(n)`, which returns
`True` once a stop is requested) so it can finish cleanly instead of being
cancelled.

**`PeriodicDaemon`** calls `tick()` every `interval` seconds, measured from the
start of one tick to the start of the next. A failing tick is logged and
retried with exponential backoff, so a database blip doesn't kill the process.
Set `max_consecutive_failures` to give up and let the supervisor restart it.

**`ServiceRunner`**:

1. runs the `on_startup` hooks, then each service's `on_start`, in order. A
   startup failure stops whatever had already started.
2. runs every `serve` concurrently.
3. shuts down on SIGINT/SIGTERM, when any service crashes, or when any service
   returns on its own (that counts as a failure).
4. cancels services that are still running after `stop_timeout`.
5. runs each `on_stop` in reverse order, then the `on_shutdown` hooks.

The exit code is 0 after a signal-driven stop and 1 after any failure, so
Docker or systemd restarts the process only when it should.

**`unit_of_work_scope(**payload)`** is the daemon's equivalent of a request: a
fresh `ExecutionContext` (with a `trace_id`), a DB session that repositories
resolve through `db.session`, and a unit of work.

### Liveness

Restarting only when the process crashes misses the worst failure a daemon
has: hanging while still alive. Every heartbeat touches
`DAEMON_HEARTBEAT_FILE`. `scripts/healthcheck.py` exits 1 once that file is
older than `DAEMON_HEARTBEAT_MAX_AGE`, or missing (the daemon removes it on
stop). Compose runs it as the `daemon` service's healthcheck. Point any other
supervisor (k8s `exec` probe, systemd watchdog script) at the same script.

---

## Telemetry

Every `logging` call becomes a structured JSON line in `logs/<service>/`. A
separate daemon (`python runner.py`) tails those files and fans them out to a
Postgres table and, optionally, Telegram. `TELEMETRY_SERVICE` names the process
writing each record.

---

## Configuration

Every setting is `<PREFIX>_<FIELD>`, where the prefix names the config class
that owns it. There are no unprefixed variables and no per-field aliases.

| Prefix | Class | Holds |
|---|---|---|
| `APP_` | `AppConfig` | environment, timezone, secrets |
| `DAEMON_` | `DaemonConfig` | heartbeat file/interval/max age, stop timeout |
| `POSTGRES_` | `DatabaseConfig` | connection |
| `REDIS_` | `RedisConfig` | connection |
| `TELEMETRY_` | `TelemetryConfig` | service name, sinks, gates |
| `TELEGRAM_` | `TelegramConfig` | alert routing |

`BasePydanticConfig` owns the file, encoding and casing rules. A config
subclass declares only its `env_prefix`. Adding a setting means adding one
field, never a field plus an alias.

**Ports are host ports.** `POSTGRES_PORT` is where postgres is published on your
machine. Inside the compose network, services use their standard ports, and
`compose.override.yml` sets those for the containers.

## Conventions

**Every id is a UUIDv7**: primary keys (`ID_T`), event ids and trace ids.
They're ordered by time, so they index like a sequence and still can't be
guessed. The app generates them (`shared_kernel/utils/functions/uuid_funcs.py`,
stdlib `uuid.uuid7` on 3.14+), and every primary key also has a
`server_default` of `uuidv7()`, so raw-SQL inserts get one too. That needs
**PostgreSQL 18+**; the compose image is 18.6.

**Tables carry a bounded-context prefix** (`billing_invoice`, `telemetry_log`).
All table names live in one enum, `data_access/orm/constants/db_constants.py`.

**Results, not exceptions, for expected failures:** `Result[T,
list[AppExceptionDetail]]`. Exceptions are for the unexpected.

**Validation is pydantic.** A domain operation takes a `DomainParams` DTO
(frozen, `extra="forbid"`) whose fields use annotated value types. Building one
validates it, so an aggregate only has to hold the invariants that span several
fields.

**One transaction per unit of work.** Repositories never commit.

### Adding a bounded context

1. `core/<context>/`: aggregate (`AggregateRoot`), entities, params, and a
   repository protocol.
2. `data_access/orm/<context>/`: ORM model (`SqlAlchemyBaseModel` + mixins) and
   a repository (`SqlAlchemyRepository`). Export the model from
   `data_access/orm/models.py` and add its table to `DatabaseTable`.
3. Register the aggregate → ORM model pair in
   `infra/constants/entity_source_consts.py`, and its name in `AggregateName`.
4. `infra/di/<context>_di.py`, mounted in `RootDIContainer`.
5. `alembic revision --autogenerate -m "add <context>"`.

---

## Migrations

```bash
alembic revision --autogenerate -m "add orders"
alembic upgrade head
alembic downgrade -1
```

`0001` creates only the telemetry tables. The database URL comes from `.env`
through `DatabaseConfig` (see `migrations/env.py`). The container start script
(`scripts/start_daemon.sh`) runs `alembic upgrade head` before `main.py`.

## Tests

```bash
pytest
```

The suite needs no database.
