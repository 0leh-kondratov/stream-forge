Вот пример **JSON-команды** для запуска очередей, необходимых **для обучения GNN** на паре `BTCUSDT` с использованием исторических данных:

---

### 📦 Пример `POST /queues/start` с множеством подзадач для GNN:

```json
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
```

---

### 🔍 Объяснение:

| Поле                | Значение                                           |
| ------------------- | -------------------------------------------------- |
| `symbol`            | Торговая пара (например, BTCUSDT)                  |
| `time_range`        | Период обучения GNN                                |
| `type`              | Указывает тип данных / действия                    |
| `interval` (опц.)   | Используется для свечей (например, 5m)             |
| `collection_inputs` | Список коллекций ArangoDB для построения графа     |
| `collection_output` | Целевая коллекция, куда `graph-builder` пишет граф |
| `model_output`      | Имя для сохранения модели в MinIO / Arango / FS    |

---

### ⚠️ Важно:

* `loader-producer` пишет в Kafka
* `arango-connector` пишет в ArangoDB
* `graph-builder` строит граф из нескольких коллекций
* `gnn-trainer` обучает модель на этом графе

---
Вот пример **JSON-команды** для запуска очередей, необходимых **для обучения GNN** на паре `BTCUSDT` с использованием исторических данных:

---

### 📦 Пример `POST /queues/start` с множеством подзадач для GNN:

```json
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
```

---

### 🔍 Объяснение:

| Поле                | Значение                                           |
| ------------------- | -------------------------------------------------- |
| `symbol`            | Торговая пара (например, BTCUSDT)                  |
| `time_range`        | Период обучения GNN                                |
| `type`              | Указывает тип данных / действия                    |
| `interval` (опц.)   | Используется для свечей (например, 5m)             |
| `collection_inputs` | Список коллекций ArangoDB для построения графа     |
| `collection_output` | Целевая коллекция, куда `graph-builder` пишет граф |
| `model_output`      | Имя для сохранения модели в MinIO / Arango / FS    |

---

### ⚠️ Важно:

* `loader-producer` пишет в Kafka
* `arango-connector` пишет в ArangoDB
* `graph-builder` строит граф из нескольких коллекций
* `gnn-trainer` обучает модель на этом графе

---

Вот пример **JSON-команды** для запуска очередей, необходимых **для обучения GNN** на паре `BTCUSDT` с использованием исторических данных:

---

### 📦 Пример `POST /queues/start` с множеством подзадач для GNN:

```json
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
```

---

### 🔍 Объяснение:

| Поле                | Значение                                           |
| ------------------- | -------------------------------------------------- |
| `symbol`            | Торговая пара (например, BTCUSDT)                  |
| `time_range`        | Период обучения GNN                                |
| `type`              | Указывает тип данных / действия                    |
| `interval` (опц.)   | Используется для свечей (например, 5m)             |
| `collection_inputs` | Список коллекций ArangoDB для построения графа     |
| `collection_output` | Целевая коллекция, куда `graph-builder` пишет граф |
| `model_output`      | Имя для сохранения модели в MinIO / Arango / FS    |

---

### ⚠️ Важно:

* `loader-producer` пишет в Kafka
* `arango-connector` пишет в ArangoDB
* `graph-builder` строит граф из нескольких коллекций
* `gnn-trainer` обучает модель на этом графе

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




