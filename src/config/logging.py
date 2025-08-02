from typing import Annotated, Literal

from pydantic import BeforeValidator, Field

from src.config.base import BaseSettingsModel

LogLevelLiteral = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormatLiteral = Literal["Pretty", "Json"]

LogLevel = Annotated[
    LogLevelLiteral,
    BeforeValidator(lambda v: v.upper()),
]


class LogSettings(BaseSettingsModel):
    level: LogLevel = "DEBUG"
    format_: LogFormatLiteral = Field(validation_alias="FORMAT", default="Pretty")
