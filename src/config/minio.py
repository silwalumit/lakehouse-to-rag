from pydantic import SecretStr

from src.config.base import BaseSettingsModel


class MinioSettings(BaseSettingsModel):
    connect_uri: str
    access_key: str | None = None
    secret_key: SecretStr | None = None
