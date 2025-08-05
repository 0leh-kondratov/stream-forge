Для **исторических данных** (через `loader-producer` + `arango-connector`) мы зафиксируем следующую спецификацию. Она пригодится как для документации, так и для Swagger/JSON-схем.

---

## 📘 QueueManager: Историческая загрузка данных (api\_\*)

### 🧩 Команда (`start`) запуска очереди

```json
{
  "command": "start",
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "symbol": "BTCUSDT",
  "type": "api_candles_5m",
  "time_range": "2024-06-01:2024-06-02",
  "targets": [
    {
      "target": "loader-producer",
      "image": "registry.dmz.home/streamforge/loader-producer:v0.1.7",
      "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
      "telemetry_id": "loader-producer__abc123"
    },
    {
      "target": "arango-connector",
      "image": "registry.dmz.home/streamforge/arango-connector:v0.1.0",
      "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
      "collection_name": "btc_candles_5m_2024_06_01",
      "telemetry_id": "arango-connector__abc123"
    }
  ],
  "timestamp": 1722346211.177
}
```

---

## 📥 Объяснение полей:

| Поле               | Обязательное           | Описание                                                               |
| ------------------ | ---------------------- | ---------------------------------------------------------------------- |
| `command`          | ✅                      | Тип команды: `start` или `stop`                                        |
| `queue_id`         | ✅                      | Стандартизированное имя очереди, включая символ, тип, дату, и short id |
| `symbol`           | ✅                      | Тикер: например, `BTCUSDT`                                             |
| `type`             | ✅                      | Исторический тип, например `api_candles_5m`, `api_trades`, `api_depth` |
| `time_range`       | ✅                      | Временной интервал загрузки, формат `YYYY-MM-DD:YYYY-MM-DD`            |
| `targets[]`        | ✅                      | Список микросервисов, которые участвуют в задаче                       |
| `targets[].target` | ✅                      | Название микросервиса: `loader-producer`, `arango-connector`           |
| `kafka_topic`      | ✅                      | Kafka топик, общий для продюсера и consumer                            |
| `collection_name`  | loader: ❌<br>arango: ✅ | Коллекция в ArangoDB, в которую писать данные                          |
| `telemetry_id`     | ✅                      | Для отправки метрик и статуса                                          |
| `image`            | ✅                      | Образ, который будет запущен в Kubernetes                              |
| `timestamp`        | ✅                      | UNIX timestamp команды                                                 |

---

Для **исторических данных** (через `loader-producer` + `arango-connector`) мы зафиксируем следующую спецификацию. Она пригодится как для документации, так и для Swagger/JSON-схем.

---

## 📘 QueueManager: Историческая загрузка данных (api\_\*)

### 🧩 Команда (`start`) запуска очереди

```json
{
  "command": "start",
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "symbol": "BTCUSDT",
  "type": "api_candles_5m",
  "time_range": "2024-06-01:2024-06-02",
  "targets": [
    {
      "target": "loader-producer",
      "image": "registry.dmz.home/streamforge/loader-producer:v0.1.7",
      "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
      "telemetry_id": "loader-producer__abc123"
    },
    {
      "target": "arango-connector",
      "image": "registry.dmz.home/streamforge/arango-connector:v0.1.0",
      "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
      "collection_name": "btc_candles_5m_2024_06_01",
      "telemetry_id": "arango-connector__abc123"
    }
  ],
  "timestamp": 1722346211.177
}
```

---

## 📥 Объяснение полей:

| Поле               | Обязательное           | Описание                                                               |
| ------------------ | ---------------------- | ---------------------------------------------------------------------- |
| `command`          | ✅                      | Тип команды: `start` или `stop`                                        |
| `queue_id`         | ✅                      | Стандартизированное имя очереди, включая символ, тип, дату, и short id |
| `symbol`           | ✅                      | Тикер: например, `BTCUSDT`                                             |
| `type`             | ✅                      | Исторический тип, например `api_candles_5m`, `api_trades`, `api_depth` |
| `time_range`       | ✅                      | Временной интервал загрузки, формат `YYYY-MM-DD:YYYY-MM-DD`            |
| `targets[]`        | ✅                      | Список микросервисов, которые участвуют в задаче                       |
| `targets[].target` | ✅                      | Название микросервиса: `loader-producer`, `arango-connector`           |
| `kafka_topic`      | ✅                      | Kafka топик, общий для продюсера и consumer                            |
| `collection_name`  | loader: ❌<br>arango: ✅ | Коллекция в ArangoDB, в которую писать данные                          |
| `telemetry_id`     | ✅                      | Для отправки метрик и статуса                                          |
| `image`            | ✅                      | Образ, который будет запущен в Kubernetes                              |
| `timestamp`        | ✅                      | UNIX timestamp команды                                                 |

---
Отлично. Для **исторических данных** (через `loader-producer` + `arango-connector`) мы зафиксируем следующую спецификацию. Она пригодится как для документации, так и для Swagger/JSON-схем.

---

## 📘 QueueManager: Историческая загрузка данных (api\_\*)

### 🧩 Команда (`start`) запуска очереди

```json
{
  "command": "start",
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "symbol": "BTCUSDT",
  "type": "api_candles_5m",
  "time_range": "2024-06-01:2024-06-02",
  "targets": [
    {
      "target": "loader-producer",
      "image": "registry.dmz.home/streamforge/loader-producer:v0.1.7",
      "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
      "telemetry_id": "loader-producer__abc123"
    },
    {
      "target": "arango-connector",
      "image": "registry.dmz.home/streamforge/arango-connector:v0.1.0",
      "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
      "collection_name": "btc_candles_5m_2024_06_01",
      "telemetry_id": "arango-connector__abc123"
    }
  ],
  "timestamp": 1722346211.177
}
```

---

## 📥 Объяснение полей:

| Поле               | Обязательное           | Описание                                                               |
| ------------------ | ---------------------- | ---------------------------------------------------------------------- |
| `command`          | ✅                      | Тип команды: `start` или `stop`                                        |
| `queue_id`         | ✅                      | Стандартизированное имя очереди, включая символ, тип, дату, и short id |
| `symbol`           | ✅                      | Тикер: например, `BTCUSDT`                                             |
| `type`             | ✅                      | Исторический тип, например `api_candles_5m`, `api_trades`, `api_depth` |
| `time_range`       | ✅                      | Временной интервал загрузки, формат `YYYY-MM-DD:YYYY-MM-DD`            |
| `targets[]`        | ✅                      | Список микросервисов, которые участвуют в задаче                       |
| `targets[].target` | ✅                      | Название микросервиса: `loader-producer`, `arango-connector`           |
| `kafka_topic`      | ✅                      | Kafka топик, общий для продюсера и consumer                            |
| `collection_name`  | loader: ❌<br>arango: ✅ | Коллекция в ArangoDB, в которую писать данные                          |
| `telemetry_id`     | ✅                      | Для отправки метрик и статуса                                          |
| `image`            | ✅                      | Образ, который будет запущен в Kubernetes                              |
| `timestamp`        | ✅                      | UNIX timestamp команды                                                 |

---

Хочешь теперь добавить вариант `stop`, или сделать Swagger/JSON Schema по этой команде?


