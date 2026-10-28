from dependency_injector import containers, providers

from src.app.infra.services.security_services import (
    AESGCMEncryptionService,
    HmacSha256SignatureService,
    SecretService,
)
from src.app.modules.cache.ports import CacheClientProto
from src.app.modules.cache.redis_client import RedisClient
from src.app.shared_kernel.di.configuration_di import ConfigurationDIContainer
from src.app.shared_kernel.ports.services.encryption import (
    EncryptionServiceProto,
    SignatureServiceProto,
)
from src.app.shared_kernel.ports.services.secrets import SecretServiceProto


class InfraServicesDIContainer(containers.DeclarativeContainer):
    # Dependencies
    config: providers.Container[ConfigurationDIContainer] = (
        providers.DependenciesContainer()
    )

    # Security
    encryption_service: providers.Provider[EncryptionServiceProto] = (
        providers.Singleton(AESGCMEncryptionService, config=config.app)
    )
    signature_service: providers.Provider[SignatureServiceProto] = providers.Singleton(
        HmacSha256SignatureService, config=config.app
    )
    secret_service: providers.Provider[SecretServiceProto] = providers.Singleton(
        SecretService
    )

    # Cache
    cache_client: providers.Provider[CacheClientProto] = providers.Singleton(
        RedisClient, config=config.redis
    )


class InfraDIContainer(containers.DeclarativeContainer):
    # Dependencies
    config: providers.Container[ConfigurationDIContainer] = (
        providers.DependenciesContainer()
    )

    # Providers
    services: providers.Container[InfraServicesDIContainer] = providers.Container(
        InfraServicesDIContainer, config=config
    )
