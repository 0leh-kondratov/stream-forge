from fastapi import APIRouter, Body, HTTPException
from loguru import logger

from app.models.commands import QueueStartRequest, StartTestFlowCommand, StartQueueCommand
from app.services.job_launcher import launch_job
from app.services.arango_service import save_queue_meta
from app.utils.naming import generate_ids
from app.services.testing_service import launch_test_flow

router = APIRouter(prefix="/queues", tags=["Queues"])


@router.post("/start-pipeline", summary="Запуск нового конвейера обработки данных", tags=["Queues"])
async def start_pipeline(request: QueueStartRequest = Body(...)):
    """
    Запускает конвейер, состоящий из одного или нескольких микросервисов.
    - Генерирует уникальный `queue_id` для всего конвейера.
    - Последовательно запускает каждый микросервис из списка `microservices` как отдельный Job в Kubernetes.
    """
    # Для конвейера используется `type` первого микросервиса для генерации ID
    primary_type = request.microservices[0].type
    ids = generate_ids(symbol=request.symbol, type_=primary_type, time_range=request.time_range)
    queue_id = ids["queue_id"]

    logger.info(f"🚀 Запуск конвейера: {queue_id} для символа {request.symbol}")

    try:
        # Сохранение метаданных о всем конвейере
        await save_queue_meta(queue_id=queue_id, command=request)

        # Запуск каждого микросервиса в конвейере
        for microservice_config in request.microservices:
            await launch_job(
                queue_id=queue_id,
                short_id=ids["short_id"],
                symbol=request.symbol,
                time_range=request.time_range,
                kafka_topic=ids["kafka_topic"],
                collection_name=ids["collection_name"], # Используем общее имя коллекции
                service_config=microservice_config,
            )
        
        logger.info(f"✅ Все задания для конвейера {queue_id} успешно запущены.")
        return {"status": "ok", "queue_id": queue_id, "ids": ids}

    except Exception as e:
        logger.exception(f"❌ Ошибка при запуске конвейера {queue_id}.")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start-test-flow", summary="Запуск стандартного тестового data-flow", tags=["Testing"])
async def start_test_flow(command: StartTestFlowCommand = Body(...)):
    """
    Запускает предопределенный тестовый data-flow (например, trades loader + arango connector).
    Принимает минимальные параметры, остальное берет из шаблона `test_flows.yaml`.
    """
    try:
        queue_id = await launch_test_flow(command)
        logger.info(f"🚀 Запущен тестовый data-flow: {queue_id}")
        return {"status": "ok", "queue_id": queue_id, "message": "Test flow started"}
    except Exception as e:
        logger.exception("❌ Ошибка запуска тестового data-flow.")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", summary="(DEPRECATED) Запуск одиночной очереди", tags=["Legacy"])
async def start_queue_legacy(command: StartQueueCommand = Body(...)):
    """
    **Устаревший метод.** Используйте `/start-pipeline`.
    Запускает одно задание в Kubernetes.
    """
    logger.warning("Вызван устаревший эндпоинт /start. Используйте /start-pipeline.")
    ids = generate_ids(symbol=command.symbol, type_=command.type, time_range=command.time_range)
    queue_id = ids["queue_id"]
    
    try:
        await save_queue_meta(queue_id=queue_id, command=command)
        # Этот эндпоинт теперь несовместим с launch_job, так как command не является MicroserviceConfig
        # Оставляем как заглушку или адаптируем, если нужно сохранить функциональность
        logger.info(f"🚀 Запуск очереди (legacy): {queue_id}")
        # await launch_job(...) # Требуется адаптация
        return {"status": "deprecated", "queue_id": queue_id, "message": "This endpoint is deprecated."}

    except Exception as e:
        logger.exception("❌ Ошибка запуска очереди (legacy).")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", summary="Список всех очередей")
async def list_queues():
    from app.services.arango_service import arango_service
    queues = await arango_service.list_all_queues()
    return {"queues": queues}


@router.post("/stop", summary="Остановка очереди по queue_id")
async def stop_queue(data: dict = Body(...)):
    from app.kafka.kafka_command import send_stop_command

    queue_id = data.get("queue_id")
    if not queue_id:
        raise HTTPException(status_code=400, detail="queue_id обязателен")

    await send_stop_command(queue_id=queue_id)
    return {"status": "stopping", "queue_id": queue_id}

