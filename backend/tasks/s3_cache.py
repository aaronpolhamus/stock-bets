from backend.database.helpers import aws_client
from config import Config


def set(name: str, value: str) -> None:
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
    value = str.encode(value)
    s3_client = aws_client()
    s3_client.put_object(Body=value, Bucket=bucket, Key=f"cache/{name}")


def unpack_s3_json(key: str):
    bucket = Config.AWS_PRIVATE_BUCKET_NAME
    s3_client = aws_client()
    object_info = s3_client.get_object(Bucket=bucket, Key=f"cache/{key}")
    value = object_info['Body'].read()
    return value.decode()
