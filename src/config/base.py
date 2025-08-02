from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings as BasePydanticSettings
from pydantic_settings import SettingsConfigDict


class BaseSettings(BasePydanticSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        validate_default=True,
    )


class BaseSettingsModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
