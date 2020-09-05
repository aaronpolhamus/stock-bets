"""This module defines a redis-like interface to the /cache directory in our applications private bucket. The idea is
to be able to use the key-value interface for storing mutable JSONs and other "semi-large" data structures in S3. Why
not just use redis, then? you might ask. To avoid expensive elastic cache scaling when a much cheaper, and only
marginally less performant implementation of S3 does the trick. The interfaces are designed to be swapable, so this
decision is easily reversible in the future."""
import json

from backend.database.helpers import aws_client
from config import Config


def set(name: str, value, endpoint_url: str = Config.AWS_ENDPOINT_URL, *_args, **_kwargs) -> None:
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
    value = str.encode(str(value))
    s3_client = aws_client(endpoint_url=endpoint_url)
    s3_client.put_object(Body=value, Bucket=bucket, Key=f"cache/{name}")


def unpack_s3_json(key: str):
    value = get(key)
    if value:
        return json.loads(value)


def get(key: str, endpoint_url: str = Config.AWS_ENDPOINT_URL):
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
    s3_client = aws_client(endpoint_url=endpoint_url)
    if s3_client.list_objects_v2(Bucket=bucket, Prefix=f"cache/{key}")["KeyCount"] > 0:
        object_info = s3_client.get_object(Bucket=bucket, Key=f"cache/{key}")
        value = object_info['Body'].read().decode()
        try:
            return float(value)
        except ValueError:
            return value


def flushall():
    objects, s3_client = get_objects()
    if objects is not None:
        keys = [{'Key': key['Key']} for key in objects]
        s3_client.delete_objects(Bucket=Config.AWS_PRIVATE_BUCKET_NAME, Delete={'Objects': keys})


def keys():
    objects, _ = get_objects()
    if objects is not None:
        return [key['Key'][6:] for key in objects]
    return []


def get_objects(endpoint_url: str = Config.AWS_ENDPOINT_URL,):
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
    s3_client = aws_client(endpoint_url=endpoint_url)
    objects = s3_client.list_objects_v2(Bucket=bucket, Prefix='cache/')
    if 'Contents' in objects:
        objects = objects['Contents']
        return objects, s3_client
    return None, None
