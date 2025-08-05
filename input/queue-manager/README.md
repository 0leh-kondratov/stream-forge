# 📦 StreamForge Queue Manager

Управляющий микросервис для запуска, остановки и мониторинга очередей обработки данных в StreamForge.

## 🚀 Возможности

- Запуск Kubernetes Job'ов: `loader-producer`, `arango-connector`, `gnn-trainer`, `visualizer`, `graph-builder`
- Поддержка параметризированного запуска через Swagger
- Управление очередями по `queue_id`
- Поддержка команд через Kafka (`queue-control`, `queue-events`)
- Поддержка Prometheus-метрик
- Встроенная health-прослойка `/health/live`, `/health/ready`, `/health/startup`

## 🛠️ Переменные окружения

Файл `.env`:

```dotenv
KAFKA_BOOTSTRAP_SERVERS=...
KAFKA_USER=...
KAFKA_PASSWORD=...
CA_PATH=...

ARANGO_URL=...
ARANGO_DB=...
ARANGO_USER=...
ARANGO_PASSWORD=...

QUEUE_CONTROL_TOPIC=queue-control
QUEUE_EVENTS_TOPIC=queue-events



queue-manager/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── logging_config.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── commands.py
│   │   ├── telemetry.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── queues.py
│   │   ├── health.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── job_launcher.py
│   │   ├── arango_service.py
│   │   ├── telemetry_dispatcher.py
│   │   ├── queue_id_generator.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── naming.py
│   │   ├── validators.py
│   ├── kafka/
│   │   ├── __init__.py
│   │   ├── kafka_command.py
│   │   ├── kafka_telemetry.py
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── prometheus_metrics.py
├── .env
├── Dockerfile
├── .gitlab-ci.yml
├── requirements.txt
└── README.md


Проверь что что с множественной загрузкой группы микросервисов ?

{
  "symbol": "BTCUSDT",
  "time_range": "2024-06-01:2024-06-30",
  "requests": [
    {
      "target": "loader-producer",
      "type": "api_candles_5m",
      "interval": "5m"
    },
    {
      "target": "loader-producer",
      "type": "api_trades"
    },
    {
      "target": "arango-connector",
      "type": "api_candles_5m"
    },
    {
      "target": "arango-connector",
      "type": "api_trades"
    },
    {
      "target": "graph-builder",
      "type": "gnn_graph",
      "collection_inputs": [
        "btc_candles_5m_2024_06",
        "btc_trades_2024_06"
      ],
      "collection_output": "btc_graph_2024_06"
    },
    {
      "target": "gnn-trainer",
      "type": "gnn_train",
      "graph_collection": "btc_graph_2024_06",
      "model_output": "gnn_model_btc_2024_06"
    }
  ]
}

{
  "symbol": "BTCUSDT",
  "time_range": "2024-08-01:2024-08-01",
  "requests": [
    {
      "target": "loader-producer",
      "type": "ws_candles_1m"
    },
    {
      "target": "loader-producer",
      "type": "ws_trades"
    },
    {
      "target": "arango-connector",
      "type": "ws_candles_1m"
    },
    {
      "target": "arango-connector",
      "type": "ws_trades"
    },
    {
      "target": "graph-builder",
      "type": "realtime_graph",
      "collection_inputs": [
        "btc_ws_candles_1m_2024_08_01",
        "btc_ws_trades_2024_08_01"
      ],
      "collection_output": "btc_graph_rt_2024_08_01"
    },
    {
      "target": "gnn-trainer",
      "type": "realtime_gnn_infer",
      "graph_collection": "btc_graph_rt_2024_08_01",
      "inference_interval": "5m"
    },
    {
      "target": "visualizer",
      "type": "graph_metrics_stream",
      "source": "btc_graph_rt_2024_08_01"
    }
  ]
}
