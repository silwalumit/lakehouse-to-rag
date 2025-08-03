from pydantic import SecretStr

from config.base import BaseSettingsModel


class MinioSettings(BaseSettingsModel):
    connect_uri: str
    access_key: str
    secret_key: SecretStr
