import yaml
from loguru import logger

from app.models.commands import StartTestFlowCommand, MicroserviceConfig, QueueStartRequest
from app.services.job_launcher import launch_job
from app.services.arango_service import arango_service
from app.utils.naming import generate_ids


def load_test_flow_template(name: str):
    try:
        with open("test_flows.yaml", "r") as f:
            templates = yaml.safe_load(f)
        return templates[name]
    except FileNotFoundError:
        logger.error("❌ Файл test_flows.yaml не найден.")
        raise
    except KeyError:
        logger.error(f"❌ Тестовый прогон '{name}' не найден в test_flows.yaml.")
        raise


async def launch_test_flow(command: StartTestFlowCommand) -> str:
    """
    Собирает полную команду из шаблона и запускает Job'ы.
    """
    logger.info(f"Запрос на запуск тестового прогона: {command.flow_name}")
    template = load_test_flow_template(command.flow_name)

    # 1. Генерируем ID для всего flow
    ids = generate_ids(
        symbol=command.symbol,
        type_=command.flow_name,
        time_range=command.time_range
    )
    queue_id = ids["queue_id"]

    # 2. Формируем полную команду на основе шаблона
    microservices = [MicroserviceConfig(**service) for service in template["services"]]
    full_command = QueueStartRequest(
        symbol=command.symbol.upper(),
        time_range=command.time_range,
        microservices=microservices
    )

    # 3. Используем существующие сервисы для сохранения и запуска
    await arango_service.save_queue_meta(queue_id=queue_id, command=full_command)

    for microservice_config in full_command.microservices:
        await launch_job(
            queue_id=queue_id,
            short_id=ids["short_id"],
            symbol=full_command.symbol,
            time_range=full_command.time_range,
            kafka_topic=ids["kafka_topic"],
            collection_name=ids["collection_name"],
            service_config=microservice_config,
        )

    logger.info(f"✅ Все задания для тестового прогона {queue_id} успешно запущены.")
    return queue_id
