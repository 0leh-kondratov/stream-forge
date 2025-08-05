Вот полная и структурированная **документация (в виде промпта)** для **перспективного микросервиса `visualizer`** проекта **StreamForge**, с поддержкой свечей, графиков, индикаторов и уровней.

---

## 📘 Документация: `visualizer` (StreamForge)

### 🧭 Назначение

Микросервис `visualizer` отвечает за отображение рыночных данных, технических индикаторов и графовых структур в виде **веб-интерфейса** (UI). Использует WebSocket и REST API для получения и отображения данных в реальном времени, а также из исторических коллекций.

---

### 🖼️ Поддерживаемые вкладки (в UI)

* `Webhooks` — события от микросервисов
* `Kafka Topic` — WebSocket-поток сообщений
* `Candlestick Chart` — отображение OHLCV
* `Heatmap Levels` — визуализация рыночных уровней
* `Indicators` — RSI, VWAP, MA и т.д.
* `GNN Output` — вероятности, классификации
* `Graph View` — визуализация графа токенов / связей

---

### 📥 Пример команды запуска из `queue-manager`

```json
{
  "command": "start",
  "queue_id": "visual-btcusdt-candles_indicators-2024_06_01-abc123",
  "target": "visualizer",
  "symbol": "BTCUSDT",
  "type": "candles_indicators",
  "telemetry_id": "visualizer__abc123",
  "image": "registry.dmz.home/streamforge/visualizer:v0.1.0",
  "timestamp": 1722347501.100
}
```

---

### 📤 Телеметрия (`queue-events`)

```json
{
  "queue_id": "visual-btcusdt-candles_indicators-2024_06_01-abc123",
  "telemetry_id": "visualizer__abc123",
  "status": "started",
  "message": "Visualizer started",
  "timestamp": 1722347510.123,
  "producer": "visualizer__abc123",
  "finished": false
}
```

```json
{
  "queue_id": "visual-btcusdt-candles_indicators-2024_06_01-abc123",
  "telemetry_id": "visualizer__abc123",
  "status": "finished",
  "message": "Visualizer shutdown (no more data)",
  "timestamp": 1722348999.456,
  "producer": "visualizer__abc123",
  "finished": true
}
```

---

### 📡 Поддержка WebSocket

```http
GET /ws/topic/{kafka_topic}
```

Получает сообщения из указанного топика и передаёт их клиенту в реальном времени.

---

### 🔧 Переменные окружения (.env или ConfigMap)

```dotenv
ARANGO_URL=http://abase-3.dmz.home:8529
ARANGO_DB=streamforge
ARANGO_USER=root
ARANGO_PASSWORD=...

KAFKA_BOOTSTRAP_SERVERS=k3-kafka-bootstrap.kafka:9093
KAFKA_USER=user-consumer-tls
KAFKA_PASSWORD=...
CA_PATH=/usr/local/share/ca-certificates/ca.crt

QUEUE_CONTROL_TOPIC=queue-control
QUEUE_EVENTS_TOPIC=queue-events
KAFKA_TOPIC=visualizer-topic
QUEUE_ID=visual-btcusdt-candles_indicators-2024_06_01-abc123

TELEMETRY_PRODUCER_ID=visualizer__abc123

# UI
FRONTEND_PATH=/app/frontend
HOST=0.0.0.0
PORT=8000
```

---

### 📦 Поддержка данных

| Источник          | Назначение                      |
| ----------------- | ------------------------------- |
| Kafka (topic)     | Получение данных по WebSocket   |
| ArangoDB          | Исторические данные свечей, RSI |
| MinIO (в будущем) | Вывод моделей GNN               |

---

### 📦 Технические компоненты

* FastAPI backend
* Jinja2 templates
* WebSocket endpoint
* Kafka consumer
* Prometheus metrics
* Поддержка фильтрации по queue\_id и symbol

---

### 🧪 Unit-тесты

* Проверка WebSocket соединения и маршрутов
* Проверка наличия и обработки данных из Kafka
* Проверка фильтрации по symbol / type
* Проверка шаблонов UI (HTML response)

---

### 🧭 Поведение

1. Получает команду запуска из `queue-control`
2. Поднимает UI и WebSocket listener
3. Обновляет вкладки на основе поступающих данных
4. Завершается по команде `stop` или при отсутствии новых данных

---

Хорошо! Ниже — продолжение в том же формате (Swagger/JSON-запросы, API-команды, поля `queue_id`, `image`, `telemetry_id`, `target`) для микросервисов **`visualizer`** и **`graph-builder`**.

---

## 🎨 `visualizer`: шаблон API-команды / Swagger

**Цель**: отобразить график по данным ArangoDB или MinIO: свечи, индикаторы, граф, модельные предсказания.

### 🔧 Пример команды `/queues/start`:

```json
{
  "command": "start",
  "queue_id": "visualize-btcusdt-2024_06_01-abc123",
  "target": "visualizer",
  "symbol": "BTCUSDT",
  "type": "plot_graph",
  "collection_name": "btc_graph_5m_2024_06_01",
  "graph_name": "btc_graph_5m_2024_06_01",
  "output_type": "html",
  "output_path": "s3://visuals/btcusdt/2024_06_01/index.html",
  "image": "registry.dmz.home/streamforge/visualizer:v0.1.0",
  "telemetry_id": "visualizer__abc123",
  "timestamp": 1722346211.177
}
```

---

### 📡 Примеры телеметрии (`queue-events`):

```json
{
  "queue_id": "visualize-btcusdt-2024_06_01-abc123",
  "status": "started",
  "telemetry_id": "visualizer__abc123",
  "message": "Начато построение графика"
}
```

```json
{
  "queue_id": "visualize-btcusdt-2024_06_01-abc123",
  "status": "finished",
  "telemetry_id": "visualizer__abc123",
  "output_path": "s3://visuals/btcusdt/2024_06_01/index.html"
}
```

