

---

## 📘 Документация: `graph-builder` (StreamForge)

### 🧭 Назначение

`graph-builder` — микросервис, формирующий графовые структуры на основе свечей, ордербуков и трейдов, записанных в ArangoDB. Графы могут быть использованы для визуализации, передачи в `gnn-trainer`, или анализа рыночных связей.

---

### 📥 Пример команды запуска из `queue-manager`

```json
{
  "command": "start",
  "queue_id": "graph-btcusdt-5m-2024_06_01-abc123",
  "target": "graph-builder",
  "symbol": "BTCUSDT",
  "type": "graph_builder_ohlcv_orderbook",
  "collection_name": "btc_graph_5m_2024_06_01",
  "input_collections": ["btc_candles_5m_2024_06_01", "btc_orderbook_2024_06_01"],
  "graph_name": "btc_graph_5m_2024_06_01",
  "telemetry_id": "graph-builder__abc123",
  "image": "registry.dmz.home/streamforge/graph-builder:v0.1.0",
  "timestamp": 1722347510.432
}
```

---

### 📤 Пример телеметрии (`queue-events`)

```json
{
  "queue_id": "graph-btcusdt-5m-2024_06_01-abc123",
  "telemetry_id": "graph-builder__abc123",
  "status": "started",
  "message": "Генерация графа начата",
  "timestamp": 1722347510.999,
  "producer": "graph-builder__abc123"
}
```

```json
{
  "queue_id": "graph-btcusdt-5m-2024_06_01-abc123",
  "telemetry_id": "graph-builder__abc123",
  "status": "finished",
  "message": "Граф построен: 105 узлов, 320 ребер",
  "timestamp": 1722348999.456,
  "producer": "graph-builder__abc123",
  "finished": true
}
```

---

### 🧱 Графовая модель

* **Вершины**:

  * `TimeNode`, `PriceLevelNode`, `VolumeNode`, `IndicatorNode`, ...
* **Рёбра**:

  * Отношения типа `leads_to`, `correlates_with`, `above_threshold`, ...

---

### 📦 Поддерживаемые входы

| Тип данных    | Источник           | Коллекция                   |
| ------------- | ------------------ | --------------------------- |
| Свечи (OHLCV) | ArangoDB           | `btc_candles_5m_2024_06_01` |
| Ордербук      | ArangoDB           | `btc_orderbook_2024_06_01`  |
| Трейды        | ArangoDB           | `btc_trades_2024_06_01`     |
| Индикаторы    | ArangoDB или MinIO | `btc_indicators_2024_06_01` |

---

### 🧩 Выходы

* ArangoDB: граф `btc_graph_5m_2024_06_01` в `graph_db`
* MinIO: экспорт JSON/Parquet графов по тайм-окнам (опц.)
* Kafka: сообщение об окончании работы

---

### ⚙️ Переменные окружения

```dotenv
ARANGO_URL=http://abase-3.dmz.home:8529
ARANGO_DB=streamforge
ARANGO_USER=root
ARANGO_PASSWORD=...

KAFKA_BOOTSTRAP_SERVERS=k3-kafka-bootstrap.kafka:9093
KAFKA_USER=user-produser-tls
KAFKA_PASSWORD=...
CA_PATH=/usr/local/share/ca-certificates/ca.crt

QUEUE_CONTROL_TOPIC=queue-control
QUEUE_EVENTS_TOPIC=queue-events

QUEUE_ID=graph-btcusdt-5m-2024_06_01-abc123
SYMBOL=BTCUSDT
TYPE=graph_builder_ohlcv_orderbook
INPUT_COLLECTIONS=btc_candles_5m_2024_06_01,btc_orderbook_2024_06_01
GRAPH_NAME=btc_graph_5m_2024_06_01
TELEMETRY_PRODUCER_ID=graph-builder__abc123
```

---

### 📌 Поведение

1. Получает команду `start` с `input_collections`
2. Загружает данные по тайм-окнам (например, по 5 минут)
3. Строит граф: вершины и связи между уровнями/объемами
4. Сохраняет граф в ArangoDB (графовая модель)
5. Передаёт статус через Kafka (queue-events)

---

### 📦 Расширения

* Возможность работы с несколькими `symbol`
* Генерация `edge weights` для обучения GNN
* Передача графа в `gnn-trainer`
* Экспорт структуры в MinIO

---
---

## 🧱 `graph-builder`: шаблон API-команды / Swagger

**Цель**: построение графов на основе данных ArangoDB (trades, orderbook, свечи и т.д.)

### 🔧 Пример команды `/queues/start`:

```json
{
  "command": "start",
  "queue_id": "graph-btcusdt-5m-2024_06_01-abc123",
  "target": "graph-builder",
  "symbol": "BTCUSDT",
  "type": "graph_build",
  "interval": "5m",
  "collections": {
    "trades": "btc_trades_2024_06_01",
    "orderbook": "btc_orderbook_2024_06_01",
    "candles": "btc_candles_5m_2024_06_01"
  },
  "graph_name": "btc_graph_5m_2024_06_01",
  "output_collection": "btc_graph_5m_2024_06_01",
  "image": "registry.dmz.home/streamforge/graph-builder:v0.1.0",
  "telemetry_id": "graph-builder__abc123",
  "timestamp": 1722346211.177
}
```

---

### 📡 Примеры телеметрии (`queue-events`):

```json
{
  "queue_id": "graph-btcusdt-5m-2024_06_01-abc123",
  "status": "started",
  "telemetry_id": "graph-builder__abc123",
  "message": "Начато построение графа"
}
```

```json
{
  "queue_id": "graph-btcusdt-5m-2024_06_01-abc123",
  "status": "finished",
  "telemetry_id": "graph-builder__abc123",
  "graph_name": "btc_graph_5m_2024_06_01"
}
```

---

### ✅ Пояснение:

| Поле           | Описание                                                      |
| -------------- | ------------------------------------------------------------- |
| `queue_id`     | Уникальный идентификатор очереди. Включает дату, symbol, type |
| `target`       | Имя микросервиса: `graph-builder`, `visualizer` и др.         |
| `telemetry_id` | Для сопоставления телеметрии с конкретной задачей             |
| `image`        | Docker-образ                                                  |
| `timestamp`    | Время создания команды                                        |
| `collections`  | Именованные коллекции для построения графа                    |
| `graph_name`   | Название итогового графа                                      |

---