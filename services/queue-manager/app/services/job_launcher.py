import time
from loguru import logger
from kubernetes import client, config
from app.config import settings # Import settings
from app.utils.naming import sanitize_name
from app.models.commands import QueueCommand # Import QueueCommand

async def launch_k8s_job(
    job_name: str,
    image: str,
    env_vars: dict,
    namespace: str,
    restart_policy: str = "Never", # "OnFailure" or "Never"
    backoff_limit: int = 4,
):
    """
    Launches a Kubernetes Job.
    """
    # Load Kubernetes configuration
    # Assumes in-cluster config if running inside a pod, otherwise ~/.kube/config
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()
    
    api_instance = client.BatchV1Api()

    # Convert env_vars dict to list of V1EnvVar objects
    container_env = [
        client.V1EnvVar(name=key, value=str(value)) for key, value in env_vars.items()
    ]

    # Define the container
    container = client.V1Container(
        name=job_name,
        image=image,
        env=container_env,
        image_pull_policy="Always", # Ensure latest image is pulled
    )

    # Define the pod template
    template = client.V1PodTemplateSpec(
        spec=client.V1PodSpec(
            restart_policy=restart_policy,
            containers=[container],
            # service_account_name="default", # You might want a specific service account
        )
    )

    # Define the job spec
    job_spec = client.V1JobSpec(
        template=template,
        backoff_limit=backoff_limit,
        # ttl_seconds_after_finished=300, # Optional: Clean up job after it finishes
    )

    # Define the job object
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=job_name, namespace=namespace),
        spec=job_spec,
    )

    try:
        api_response = api_instance.create_namespaced_job(body=job, namespace=namespace)
        logger.info(f"Kubernetes Job '{job_name}' created. Status='{api_response.status}'")
        return api_response
    except client.ApiException as e:
        logger.error(f"Error creating Kubernetes Job '{job_name}': {e}")
        raise


async def launch_jobs(queue_id: str, command: QueueCommand): # Changed command type to QueueCommand
    """
    Launches a Kubernetes Job for the given command.
    """
    namespace = settings.K8S_NAMESPACE # Use namespace from settings

    job_name = f"{sanitize_name(queue_id)}-{sanitize_name(command.target)}".lower()
    
    # Construct environment variables for the job
    env_vars = {
        "QUEUE_ID": queue_id,
        "SYMBOL": command.symbol,
        "TYPE": command.type,
        "KAFKA_TOPIC": command.kafka_topic,
        "TELEMETRY_PRODUCER_ID": command.telemetry_id,
        "KAFKA_BOOTSTRAP_SERVERS": settings.KAFKA_BOOTSTRAP_SERVERS,
        "KAFKA_USER_PRODUCER": settings.KAFKA_USER, # Assuming queue-manager uses KAFKA_USER for producer
        "KAFKA_PASSWORD_PRODUCER": settings.KAFKA_PASSWORD, # Assuming queue-manager uses KAFKA_PASSWORD for producer
        "CA_PATH": settings.CA_PATH,
        "QUEUE_CONTROL_TOPIC": settings.QUEUE_CONTROL_TOPIC,
        "QUEUE_EVENTS_TOPIC": settings.QUEUE_EVENTS_TOPIC,
        "ARANGO_URL": settings.ARANGO_URL,
        "ARANGO_DB": settings.ARANGO_DB,
        "ARANGO_USER": settings.ARANGO_USER,
        "ARANGO_PASSWORD": settings.ARANGO_PASSWORD,
        # Add other specific variables if they exist in command
    }
    if command.time_range:
        env_vars["TIME_RANGE"] = command.time_range
    if command.interval:
        env_vars["INTERVAL"] = command.interval
    if command.collection_name:
        env_vars["COLLECTION_NAME"] = command.collection_name
    
    # Add image specific to the target microservice
    image_to_use = command.image
    if not image_to_use: # Fallback to images defined in settings if not in command
        if command.target == "loader-producer":
            image_to_use = settings.LOADER_IMAGE
        elif command.target == "arango-connector":
            image_to_use = settings.CONSUMER_IMAGE # Assuming CONSUMER_IMAGE is arango-connector
        elif command.target == "gnn-trainer":
            image_to_use = settings.GNN_TRAINER_IMAGE
        elif command.target == "visualizer":
            image_to_use = settings.VISUALIZER_IMAGE
        elif command.target == "graph-builder":
            image_to_use = settings.GRAPH_BUILDER_IMAGE
        else:
            logger.error(f"Unknown target microservice: {command.target}. Cannot determine image.")
            raise ValueError(f"Unknown target microservice: {command.target}")

    await launch_k8s_job(
        job_name=job_name,
        image=image_to_use,
        env_vars=env_vars,
        namespace=namespace
    )