import time
from loguru import logger
from kubernetes import client, config
from app.utils.naming import sanitize_name


async def launch_jobs(queue_id: str, command: StartQueueCommand):
    """
    Запускает Kubernetes Jobs для каждого сервиса в команде.
    """
    namespace = "streamforge" # Или любое другое пространство имен

    for service in command.services:
        job_name = f"{sanitize_name(queue_id)}-{service.name}".lower()
        kafka_topic = f"{queue_id}-{service.type}-data"
        collection_name = f"{command.symbol.lower()}_{service.type}_{command.time_range.split(':')[0]}"

        env_vars = {
            "QUEUE_ID": queue_id,
            "SYMBOL": command.symbol,
            "TYPE": service.type,
            "TIME_RANGE": command.time_range,
            "KAFKA_TOPIC": kafka_topic,
            "COLLECTION_NAME": collection_name,
            "TELEMETRY_ID": f"{service.name}_{queue_id}",
        }

        launch_k8s_job(
            job_name=job_name,
            image=service.image,
            env_vars=env_vars,
            namespace=namespace
        )
