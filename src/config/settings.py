from config.base import BaseSettings
from config.logging import LogSettings
from config.minio import MinioSettings


class Settings(BaseSettings):
    minio: MinioSettings
    log: LogSettings
