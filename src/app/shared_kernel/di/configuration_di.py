from dependency_injector import containers, providers

from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.config.infra_configs import (
    DaemonConfig,
    DatabaseConfig,
    RedisConfig,
)


class ConfigurationDIContainer(containers.DeclarativeContainer):
    db: providers.Provider[DatabaseConfig] = providers.Singleton(DatabaseConfig)
    app: providers.Provider[AppConfig] = providers.Singleton(AppConfig)
    redis: providers.Provider[RedisConfig] = providers.Singleton(RedisConfig)
    daemon: providers.Provider[DaemonConfig] = providers.Singleton(DaemonConfig)
