import os
import boto3
from botocore.vendored import requests

USER = os.getenv("RMQ_USER")
PASSWORD = os.getenv("RMQ_PASSWORD")

cloudwatch_client = boto3.client(service_name='cloudwatch', endpoint_url="https://MYCLOUDWATCHURL.monitoring.us-east-1.vpce.amazonaws.com")
ecs_client = boto3.client(service_name='ecs', endpoint_url="https://vpce-MYECSURL.ecs.us-east-1.vpce.amazonaws.com")


def get_message_count(user=USER, password=PASSWORD, domain="rabbitmq.stockbets.io/api/queues"):
    url = f"https://{user}:{password}@{domain}"
    res = requests.get(url)
    message_count = 0
    for queue in res.json():
        message_count += queue["messages"]
    print(f"message count: {message_count}")
    return message_count


def get_worker_count():
    worker_data = ecs_client.describe_services(cluster="prod", services=["worker"])
    worker_count = len(worker_data["services"])
    print(f"worker_count count: {worker_count}")
    return worker_count


def lambda_handler(event, context):
    message_count = get_message_count()
    worker_count = get_worker_count()
    print(f"msgs per worker: {message_count / worker_count}")
    metric_data = [
        {'MetricName': 'MessagesPerWorker', "Unit": "MsgsPerWorker", 'Value': message_count / worker_count},
        {'MetricName': 'NTasks', "Unit": "WorkerCount", 'Value': worker_count}
    ]
    cloudwatch_client.put_metric_data(MetricData=metric_data, Namespace="RabbitMQ")
