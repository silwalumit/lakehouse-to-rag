import io
import logging
from typing import Optional

from minio import Minio, S3Error

logger = logging.getLogger(__name__)


class MinioIOService:
    def __init__(
        self,
        endpoint: str,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure=False,
    ):
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def ensure_bucket(self, bucket):
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
            logging.info(f"Created bucket: {bucket}")

    def upload(
        self,
        bucket: str,
        object_name: str,
        data: bytes | str,
        content_type: str = "text/plain",
    ):
        self.ensure_bucket(bucket)

        if isinstance(data, str):
            data = data.encode("utf-8")

        self.client.put_object(
            bucket,
            object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        logging.info(f"Uploaded {object_name} to {bucket}")

    def download(self, bucket, object_name):
        try:
            return self.client.get_object(bucket, object_name).read()
        except S3Error as e:
            logging.error(f"Download error: {e}")
            return None

    def list_objects(self, bucket, prefix="", recursive=True):
        return self.client.list_objects(bucket, prefix=prefix, recursive=recursive)
