# 🧠 gnn-trainer

Микросервис в экосистеме **StreamForge**, предназначенный для обучения моделей графовых нейронных сетей (GNN) на основе рыночных данных.

## 🎯 Назначение

`gnn-trainer` выполняет следующие задачи:

1.  **Собирает** рыночные данные (K-lines, стакан, ставки финансирования) с Binance API.
2.  **Генерирует** признаки узлов и веса ребер для построения динамического графа рынка.
3.  **Строит** объект графа PyTorch Geometric (PyG).
4.  **Обучает** GNN-модель для прогнозирования краткосрочного движения цен.
5.  **Сохраняет** обученную модель в Minio.

Этот сервис является stateless-воркером и предназначен для запуска в виде **Kubernetes Job**. Всю необходимую конфигурацию он получает через переменные окружения.

## ⚙️ Переменные окружения

Сервис полностью настраивается через переменные окружения.

| Переменная                 | Описание                                                              | Пример                                           |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| **`QUEUE_ID`**             | Уникальный идентификатор всего workflow.                              | `wf-gnn-train-20240801-a1b2c3`                    |
| **`SYMBOL``**              | Символ или идентификатор данных (для телеметрии).                     | `MARKET_GRAPH`                                   |
| **`TYPE`**                 | Тип данных, который обрабатывается (для телеметрии).                 | `gnn_model_training`                             |
| **`TELEMETRY_PRODUCER_ID`**| Уникальный ID этого экземпляра для телеметрии.                        | `gnn-trainer__a1b2c3`                            |
| `BINANCE_API_KEY`          | API ключ для доступа к Binance API.                                   | `your_binance_api_key`                           |
| `BINANCE_API_SECRET`       | API секрет для доступа к Binance API.                                 | `your_binance_api_secret`                        |
| `KAFKA_BOOTSTRAP_SERVERS`  | Адреса брокеров Kafka (для телеметрии и, возможно, триггеров).        | `kafka-bootstrap.kafka:9093`                     |
| `KAFKA_USER`               | Имя пользователя для аутентификации в Kafka.                          | `user-producer-tls`                              |
| `KAFKA_PASSWORD`           | Пароль для пользователя Kafka.                                        | `your_kafka_password`                            |
| `CA_PATH`                  | Путь к CA-сертификату для TLS-соединения с Kafka.                     | `/certs/ca.crt`                                  |
| `QUEUE_CONTROL_TOPIC`      | Топик для получения управляющих команд (например, `stop`).            | `queue-control`                                  |
| `QUEUE_EVENTS_TOPIC`       | Топик для отправки событий телеметрии.                                | `queue-events`                                   |
| `ARANGO_URL`               | URL для подключения к ArangoDB (для загрузки графовых данных).        | `http://arango-cluster.db:8529`                  |
| `ARANGO_DB`                | Имя базы данных в ArangoDB.                                           | `streamforge`                                    |
| `ARANGO_USER`              | Пользователь для подключения к ArangoDB.                              | `root`                                           |
| `ARANGO_PASSWORD`          | Пароль для ArangoDB.                                                  | `your_arango_password`                           |
| `GRAPH_COLLECTION_NAME`    | Имя коллекции в ArangoDB, где хранятся подготовленные графовые данные.| `prepared_graph_data`                            |
| `MINIO_ENDPOINT`           | Эндпоинт Minio для сохранения моделей.                                | `minio.minio:9000`                               |
| `MINIO_ACCESS_KEY`         | Access Key для Minio.                                                 | `minio_access_key`                               |
| `MINIO_SECRET_KEY`         | Secret Key для Minio.                                                 | `minio_secret_key`                               |
| `MINIO_BUCKET_NAME`        | Имя бакета Minio для сохранения моделей.                              | `gnn-models`                                     |
| `MODEL_NAME`               | Имя сохраняемой модели.                                               | `market_gnn_v1`                                  |
| `EPOCHS`                   | Количество эпох обучения.                                             | `100`                                            |
| `LEARNING_RATE`            | Скорость обучения.                                                    | `0.001`                                          |

---

## 📡 Телеметрия (Topic: `queue-events`)

Сервис отправляет события о своем состоянии в топик `queue-events`. Это позволяет `queue-manager` отслеживать прогресс выполнения задачи.

**Пример события `loading`:**

```json
{
  "queue_id": "wf-gnn-train-20240801-a1b2c3",
  "symbol": "MARKET_GRAPH",
  "type": "gnn_model_training",
  "status": "loading",
  "message": "Эпоха 50 завершена, loss: 0.0123",
  "finished": false,
  "producer": "gnn-trainer__a1b2c3",
  "timestamp": 1722445567.890,
  "extra": {"epoch": 50, "loss": 0.0123}
}
```

**Возможные статусы:** `started`, `loading`, `interrupted`, `error`, `finished`.

---

## 🔄 Управление (Topic: `queue-control`)

Сервис слушает топик `queue-control` и реагирует на команды, адресованные его `queue_id`.

**Команда `stop`:**

```json
{
  "command": "stop",
  "queue_id": "wf-gnn-train-20240801-a1b2c3"
}
```

При получении этой команды сервис корректно завершает свою работу.
