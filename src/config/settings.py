from src.config.base import BaseSettings
from src.config.logging import LogSettings
from src.config.minio import MinioSettings


class Settings(BaseSettings):
    minio: MinioSettings
    log: LogSettings
