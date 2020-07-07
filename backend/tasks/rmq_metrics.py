import boto3
from botocore.vendored import requests

cloudwatch_client = boto3.client('cloudwatch')
client = boto3.client('ecs')

def get_message_count(user="user", password="password", domain="rabbitmq.stockbets.io/api/queues"):
    url = f"https://{user}:{password}@{domain}"
    res = requests.get(url)
    message_count = 0
    for queue in res.json():
        message_count += queue["messages"]
    print(f"message count: {message_count}")
    return message_count


def get_worker_count():
    worker_data = client.describe_services(cluster="prod", services=["worker"])
    worker_count = len(worker_data["services"])
    print(f"worker_count count: {worker_count}")
    return worker_count


def lambda_handler(event, context):
    message_count = get_message_count()
    worker_count = get_worker_count()
    metric_data = [{'MetricName': 'MessagesPerWorker', "Unit": "None", 'Value': messages / worker}]
    cloudwatch_client.put_metric_data(MetricData=metric_data, Namespace="RabbitMQ")
