from dependency_injector import containers, providers

from src.app.infra.di.db_di import DatabaseDIContainer
from src.app.infra.di.infra_di import InfraDIContainer
from src.app.infra.services.clock import Clock
from src.app.shared_kernel.di.configuration_di import ConfigurationDIContainer
from src.app.shared_kernel.di.core_di import CoreDIContainer, CoreServicesDIContainer


class RootDIContainer(containers.DeclarativeContainer):
    config: providers.Container[ConfigurationDIContainer] = providers.Container(
        ConfigurationDIContainer
    )

    # Layers
    core: providers.Container[CoreDIContainer] = providers.Container(
        CoreDIContainer,
        config=config,
        services=providers.Container(
            CoreServicesDIContainer,
            clock=providers.Singleton(Clock, tz_=config.app.provided.tzinfo),
        ),
    )

    db: providers.Container[DatabaseDIContainer] = providers.Container(
        DatabaseDIContainer,
        core=core,
    )

    infra: providers.Container[InfraDIContainer] = providers.Container(
        InfraDIContainer,
        config=config,
    )

    # Bounded contexts from `core` get their own container here.
