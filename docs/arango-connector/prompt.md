
---

## 📘 Документация: Arango-Connector (StreamForge)

### 🧭 Назначение

Микросервис `arango-connector` получает данные из Kafka, сохраняет их в ArangoDB, рассчитывает технические индикаторы (RSI, VWAP, Volatility, EMA и т.п.), а также может участвовать в построении графов (если это его профиль). Поддерживает остановку по команде из Kafka и отправляет телеметрию в `queue-events`.

---

### 🔌 Входные данные

| Источник    | Тип                   | Описание                                      |
| ----------- | --------------------- | --------------------------------------------- |
| Kafka Topic | `str`                 | Уникальный топик, из которого читаются данные |
| Очередь     | `queue_id`            | Идентификатор очереди                         |
| Команда     | Kafka `queue-control` | Поддерживает команду `stop`                   |
| Переменные  | `.env`                | Параметры подключения и конфигурации          |

---

### 🔧 Поддерживаемые `type` очередей

* `api_candles_5m`, `api_candles_1h`, ...
* `ws_candles_1m`, `ws_trades`, `ws_orderbook`
* `graph_nodes`, `graph_edges` — если тип графовый (в зависимости от сборки)

---

### 🧾 Пример команды запуска

```json
{
  "command": "start",
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "target": "arango-connector",
  "symbol": "BTCUSDT",
  "type": "api_candles_5m",
  "collection_name": "btc_candles_5m_2024_06_01",
  "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
  "telemetry_id": "arango-connector__abc123",
  "image": "registry.dmz.home/streamforge/arango-connector:v0.1.0",
  "timestamp": 1722346211.177
}
```

---

### 📤 Телеметрия (`queue-events`)

Примеры сообщений телеметрии от `arango-connector`:

```json
{
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "telemetry_id": "arango-connector__abc123",
  "status": "started",
  "records_written": 0,
  "message": "Arango connector started",
  "timestamp": 1722346211.222,
  "producer": "arango-connector__abc123",
  "finished": false
}
```

```json
{
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "telemetry_id": "arango-connector__abc123",
  "status": "finished",
  "records_written": 15340,
  "message": "All data stored",
  "timestamp": 1722346299.1,
  "producer": "arango-connector__abc123",
  "finished": true
}
```

---

### ⚙️ Важные переменные `.env`

```dotenv
ARANGO_URL=http://abase-3.dmz.home:8529
ARANGO_DB=streamforge
ARANGO_USER=root
ARANGO_PASSWORD=...

KAFKA_BOOTSTRAP_SERVERS=k3-kafka-bootstrap.kafka:9093
KAFKA_USER=user-consumer-tls
KAFKA_PASSWORD=...
QUEUE_CONTROL_TOPIC=queue-control
QUEUE_EVENTS_TOPIC=queue-events
CA_PATH=/usr/local/share/ca-certificates/ca.crt

QUEUE_ID=loader-btcusdt-api_candles_5m-2024_06_01-abc123
KAFKA_TOPIC=loader-btcusdt-api-candles-5m-2024-06-01-abc123
COLLECTION_NAME=btc_candles_5m_2024_06_01
TELEMETRY_PRODUCER_ID=arango-connector__abc123
```

---

### 🧪 Unit-тесты

* Проверка вставки валидного документа в Arango
* Обработка невалидных JSON-сообщений
* Проверка graceful shutdown по `stop_event`
* Моки Kafka consumer и Arango client

---

### 🏁 Поведение при запуске

1. Подключается к Kafka и ArangoDB
2. Слушает topic с нужным group\_id
3. Читает сообщения, пишет в коллекцию ArangoDB
4. Вычисляет индикаторы (опционально)
5. Отправляет телеметрию
6. Завершается при поступлении команды `stop`

---



