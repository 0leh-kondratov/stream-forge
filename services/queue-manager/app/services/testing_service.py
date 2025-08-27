import yaml
from loguru import logger
from app.models.commands import StartQueueCommand, StartTestFlowCommand
from app.services.job_launcher import launch_jobs
from app.services.arango_service import save_queue_meta
from app.services.queue_id_generator import generate_queue_id


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

    # 1. Генерируем общий ID для всего flow
    queue_id = generate_queue_id(
        symbol=command.symbol,
        type_=command.flow_name,
        time_range=command.time_range
    )

    # 2. Формируем полную команду на основе шаблона
    # Мы передаем список сервисов в StartQueueCommand
    full_command_data = {
        "symbol": command.symbol.upper(),
        "time_range": command.time_range,
        "services": template["services"]
    }
    full_command = StartQueueCommand(**full_command_data)

    # 3. Используем существующие сервисы для сохранения и запуска
    await save_queue_meta(queue_id=queue_id, command=full_command)
    await launch_job(queue_id=queue_id, command=full_command)

    return queue_id
