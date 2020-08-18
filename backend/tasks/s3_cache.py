import json

from backend.database.helpers import aws_client
from config import Config


def set(name: str, value, *_args, **_kwargs) -> None:
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
    value = str.encode(str(value))
    s3_client = aws_client()
    s3_client.put_object(Body=value, Bucket=bucket, Key=f"cache/{name}")


def unpack_s3_json(key: str):
    value = get(key)
    if value:
        return json.loads(value)


def get(key: str):
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
    s3_client = aws_client()
    if s3_client.list_objects_v2(Bucket=bucket, Prefix=f"cache/{key}")["KeyCount"] > 0:
        object_info = s3_client.get_object(Bucket=bucket, Key=f"cache/{key}")
        value = object_info['Body'].read().decode()
        try:
            return float(value)
        except ValueError:
            return value


def flushall():
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
