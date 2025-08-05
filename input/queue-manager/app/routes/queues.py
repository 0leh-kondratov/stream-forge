from fastapi import APIRouter, Body, HTTPException
from loguru import logger

from app.models.commands import StartQueueCommand, StartTestFlowCommand
from app.services.job_launcher import launch_jobs
from app.services.arango_service import save_queue_meta
from app.services.queue_id_generator import generate_queue_id
from app.services.testing_service import launch_test_flow

router = APIRouter(prefix="/queues", tags=["Queues"])


@router.post("/start-test-flow", summary="Запуск стандартного тестового data-flow", tags=["Testing"])
async def start_test_flow(command: StartTestFlowCommand = Body(...)):
    """
    Запускает предопределенный тестовый data-flow (например, trades loader + arango connector).
    Принимает минимальные параметры, остальное берет из шаблона `test_flows.yaml`.
    Идеально для использования через Swagger UI.
    """
    try:
        queue_id = await launch_test_flow(command)
        logger.info(f"🚀 Запущен тестовый data-flow: {queue_id}")
        return {"status": "ok", "queue_id": queue_id, "message": "Test flow started"}

    except Exception as e:
        logger.exception("❌ Ошибка запуска тестового data-flow.")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", summary="(Legacy) Запуск новой очереди", tags=["Legacy"])
async def start_queue(command: StartQueueCommand = Body(...)):
    try:
        queue_id = generate_queue_id(
            symbol=command.symbol,
            type_=command.type,
            time_range=command.time_range
        )
        logger.info(f"🚀 Запуск очереди: {queue_id}")

        await save_queue_meta(queue_id=queue_id, command=command)
        await launch_jobs(queue_id=queue_id, command=command)

        return {"status": "ok", "queue_id": queue_id}

    except Exception as e:
        logger.exception("❌ Ошибка запуска очереди.")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", summary="Список всех очередей")
async def list_queues():
    from app.services.arango_service import list_all_queues
    queues = await list_all_queues()
    return {"queues": queues}


@router.post("/stop", summary="Остановка очереди по queue_id")
async def stop_queue(data: dict = Body(...)):
    from app.kafka.kafka_command import send_stop_command

    queue_id = data.get("queue_id")
    if not queue_id:
        raise HTTPException(status_code=400, detail="queue_id обязателен")

    await send_stop_command(queue_id=queue_id)
    return {"status": "stopping", "queue_id": queue_id}

