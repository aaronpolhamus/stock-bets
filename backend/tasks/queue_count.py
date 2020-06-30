import boto3
from botocore.vendored import requests

cloudwatch_client = boto3.client('cloudwatch')


def get_queue_count(user="user", password="password", domain="rabbitmq.stockbets.io/api/queues"):
    url = f"https://{user}:{password}@{domain}"
    res = requests.get(url)
    message_count = 0
    for queue in res.json():
        message_count += queue["messages"]
    return message_count


def lambda_handler(event, context):
    metric_data = [{'MetricName': 'RabbitMQQueueLength', "Unit": "None", 'Value': get_queue_count()}]
    cloudwatch_client.put_metric_data(MetricData=metric_data, Namespace="RabbitMQ")
