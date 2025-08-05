
### 🔧 ЦЕЛЬ

Разработать и масштабировать **StreamForge** — event-driven платформу для загрузки, обработки, агрегации и анализа криптоданных (Binance), c сохранением в ArangoDB и обучением GNN.
Архитектура основана на **микросервисах**, управляемых централизованным компонентом `queue-manager`.

### 🧱 ОБЩАЯ АРХИТЕКТУРА

#### Компоненты:

1. **queue-manager** (FastAPI)
2. **loader-producer** — для получения данных с Binance (REST/WebSocket)
3. **arango-connector** — consumer Kafka, пишет данные в ArangoDB
4. **visualizer** — UI и API для отображения свечей, индикаторов и уровней
5. **graph-builder** — строит граф из ArangoDB данных
6. **gnn-trainer** — обучение GNN на графах
7. (**minio**) — опционально для хранения моделей и артефактов

#### Базовые ресурсы:

* Kafka topics
* ArangoDB коллекции
* Kubernetes Jobs
* TLS/SCRAM авторизация Kafka
* Telemetry через `queue-events` topic
* Управление через `queue-control` topic

---

### 📦 queue-manager

#### Назначение:

* Управление очередями (создание, запуск, остановка)
* Генерация и отправка Kafka-команд
* Мониторинг состояний и телеметрии
* UI-интерфейс с запуском нескольких микросервисов в одной очереди

#### Основные функции:

* Формирование `queue_id` и `telemetry_id` по шаблону
* Запуск Job’ов: `loader-producer`, `arango-connector`, `graph-builder`, `gnn-trainer`, `visualizer`
* Поддержка множественных подочередей для разных `TYPE` (например: `api_candles_5m`, `ws_orderbook`)
* Swagger-схема с вложенным списком микросервисов
* Валидация параметров очередей и подочередей
* Отображение состояния, логов, кнопки Stop
* WebSocket подписка на `queue-events` телеметрию
* Генерация Kafka-команд с target, image, timestamp, collection\_name

---

### 📊 Типы данных (TYPE)

| Тип              | Описание             | Источник  | Используется       |
| ---------------- | -------------------- | --------- | ------------------ |
| `api_candles_5m` | Исторические свечи   | REST API  | GNN, визуализация  |
| `api_trades`     | Исторические трейды  | REST API  | граф, GNN          |
| `ws_candles_5m`  | Realtime свечи       | WebSocket | визуализация       |
| `ws_trades`      | Realtime трейды      | WebSocket | визуализация, граф |
| `ws_orderbook`   | Orderbook обновления | WebSocket | граф, индикаторы   |

* Возможно добавление `depth_snapshot`, `funding_rate`, `liquidations`, `index_price`, и т.д.

---

## 🏷 Форматы идентификаторов и имени очереди

`queue-manager` должен **автоматически генерировать** имена и идентификаторы на основе входных параметров `symbol`, `type`, `time_range`, и уникального `short-id`.

| Поле              | Формат / Правило                                                                 |
| ----------------- | -------------------------------------------------------------------------------- |
| `queue_id`        | `loader-{symbol}-{type}-{startdate}-{shortid}`                                   |
| `kafka_topic`     | `{queue_id}` (используется в Kafka Producer и Consumer)                          |
| `telemetry_id`    | `{microservice_name}__{shortid}`                                                 |
| `collection_name` | `{symbol}_{data_kind}_{interval}_{date}` (например: `btc_candles_5m_2024_06_01`) |
| `pod_id`          | аналогично queue\_id, используется в Kubernetes Job/Pod                          |

Пример:

```env
symbol = BTCUSDT
type = api_candles_5m
start_date = 2024-06-01
shortid = abc123

queue_id = loader-btcusdt-api_candles_5m-2024_06_01-abc123
kafka_topic = loader-btcusdt-api-candles-5m-2024-06-01-abc123
telemetry_id = loader-producer__abc123
collection_name = btc_candles_5m_2024_06_01
```

---

## 🧬 Поддерживаемые значения `type`

В `queue-manager` необходимо поддерживать валидацию и нормализацию параметра `type`, определяющего:

* источник данных (api / ws)
* вид данных (candles, trades, depth)
* интервал (1m, 5m, ...)

### Поддерживаемые группы `type`

| Категория        | Префикс       | Примеры                            | Описание                            |
| ---------------- | ------------- | ---------------------------------- | ----------------------------------- |
| История свечей   | `api_candles` | `api_candles_1m`, `api_candles_5m` | Загрузка свечей из Binance REST API |
| История торгов   | `api_trades`  | `api_trades`                       | Исторические сделки                 |
| WebSocket свечи  | `ws_candles`  | `ws_candles_1m`                    | Реальное время, свечи               |
| WebSocket сделки | `ws_trades`   | `ws_trades`                        | Поток сделок в реальном времени     |
| WebSocket стакан | `ws_depth`    | `ws_depth`                         | Обновления стакана (orderbook)      |

---

## ✅ Валидация в FastAPI (Pydantic)

Создаётся `pydantic.BaseModel` с валидацией:

```python
class MicroserviceSpec(BaseModel):
    target: Literal["loader-producer", "arango-connector", "graph-builder", "gnn-trainer", "visualizer"]
    type: str  # validated via regex or list
    symbol: constr(strip_whitespace=True, to_upper=True)
    time_range: Optional[str]
    telemetry_id: Optional[str]
    image: Optional[str]
    kafka_topic: Optional[str]
    collection_name: Optional[str]
```

## 📡 Телеметрия (topic: `queue-events`)

Каждый микросервис (`loader-producer`, `arango-connector`, `graph-builder`, `gnn-trainer`) отправляет **события телеметрии** в Kafka-топик `queue-events`.

### Структура события:

```json
{
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "symbol": "BTCUSDT",
  "type": "api_candles_5m",
  "status": "loading",
  "message": "Загрузка продолжается",
  "records_written": 1234,
  "finished": false,
  "producer": "loader-producer__abc123",
  "timestamp": 1722346443.051
}
```

### Возможные `status`:

* `started` – микросервис начал работу
* `loading` – активная отправка или запись данных
* `interrupted` – остановлено по команде
* `error` – фатальная ошибка
* `finished` – завершено успешно

---

## 🔄 Команды управления (topic: `queue-control`)

Поддерживаемые команды:

```json
{
  "command": "stop",
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "target": "loader-producer"
}
```

Можно отправлять **массовые команды**, фильтруя по `queue_id`, `symbol`, `target`, `telemetry_id`.

---

## 🧠 Real-time vs Обучение (type)

| `type`           | Режим     | Источник          | Сервис          | Характеристики               |
| ---------------- | --------- | ----------------- | --------------- | ---------------------------- |
| `api_candles_5m` | Обучение  | REST Binance      | loader-producer | Исторические свечи           |
| `ws_candles_5m`  | Real-time | WebSocket Binance | loader-ws       | Агрегированная online свеча  |
| `ws_trades`      | Real-time | WebSocket Binance | loader-ws       | Поток трейдов                |
| `ws_orderbook`   | Real-time | WebSocket Binance | loader-ws       | Стакан (partial book, depth) |

> Примеры микросервисов: `loader-producer`, `loader-ws`, `arango-connector`, `arango-orderbook`, `graph-builder`, `gnn-trainer`, `visualizer`.

---

## 📈 Метрики (Prometheus)

### `queue-manager`

* `http_requests_total` — общее количество запросов
* `queue_requests_total{endpoint="start"}` — операции запуска
* `queue_stop_total` — количество остановок очередей

### `loader-producer`

* `records_sent_total`
* `loading_duration_seconds`
* `last_kafka_offset`

### `arango-connector`

* `records_written_total`
* `collection_upserts_total`
* `consume_latency_seconds`

---

## 🧪 Реализация остановки

Каждый микросервис слушает `queue-control` (KafkaConsumer):

```python
async for cmd in KafkaControlConsumer(queue_id).listen():
    if cmd["command"] == "stop":
        stop_event.set()
```

Завершает:

* Kafka consumer/producer
* WebSocket
* Отправляет финальную телеметрию

---

## 🔤 Алгоритм именования очередей и компонентов

> Все ключевые ресурсы (queue\_id, topic, pod, telemetry\_id) формируются по стандарту:

```
[prefix]-[symbol]-[type]-[date]-[shortid]
```

| Элемент            | Пример                                            |
| ------------------ | ------------------------------------------------- |
| queue\_id          | `loader-btcusdt-api_candles_5m-2024_06_01-abc123` |
| kafka\_topic       | `loader-btcusdt-api-candles-5m-2024-06-01-abc123` |
| telemetry\_id      | `arango-connector__abc123`                        |
| collection\_name   | `btc_candles_5m_2024_06_01`                       |
| job name           | `queue-loader-btcusdt-api-20240601-abc123`        |
| pod name (K8s)     | автоматически от StatefulSet по job name          |
| command\_id (UUID) | `cmd__UUIDv4`                                     |

---

## 🧾 Пример очереди (обучение GNN, исторические данные)

```json
{
  "command": "start",
  "queue_id": "loader-btcusdt-api_candles_5m-2024_06_01-abc123",
  "symbol": "BTCUSDT",
  "type": "api_candles_5m",
  "time_range": "2024-06-01:2024-06-02",
  "target": "loader-producer",
  "kafka_topic": "loader-btcusdt-api-candles-5m-2024-06-01-abc123",
  "telemetry_id": "loader-producer__abc123",
  "collection_name": "btc_candles_5m_2024_06_01",
  "image": "registry.dmz.home/streamforge/loader-producer:v0.1.7",
  "timestamp": 1722346211.177
}
```

---

## 🧾 Пример очереди (реальный режим, стакан ордеров)

```json
{
  "command": "start",
  "queue_id": "loader-btcusdt-ws_orderbook-2024_08_02-xyz789",
  "symbol": "BTCUSDT",
  "type": "ws_orderbook",
  "target": "loader-ws",
  "kafka_topic": "loader-btcusdt-ws-orderbook-2024-08-02-xyz789",
  "telemetry_id": "loader-ws__xyz789",
  "collection_name": "btc_orderbook_2024_08_02",
  "image": "registry.dmz.home/streamforge/loader-ws-orderbook:v0.1.0",
  "timestamp": 1722347282.889
}
```

---

## 🧩 Swagger / FastAPI-интеграция

Модель API запроса на запуск очереди (в `pydantic`):

```python
class MicroserviceConfig(BaseModel):
    target: Literal["loader-producer", "arango-connector", "graph-builder", "gnn-trainer"]
    type: str
    image: str
    telemetry_id: str
    kafka_topic: str
    collection_name: Optional[str] = None


class QueueStartRequest(BaseModel):
    command: Literal["start"]
    queue_id: str
    symbol: str
    time_range: Optional[str] = None
    microservices: List[MicroserviceConfig]
```

Swagger UI от FastAPI отобразит структуру и опишет каждое поле.

---

## 📦 env-файл и переменные

> Унифицированный `.env` подходит для всех микросервисов:

```dotenv
# Kafka
KAFKA_BOOTSTRAP_SERVERS=k3-kafka-bootstrap.kafka:9093
KAFKA_USER=user-produser-tls
KAFKA_PASSWORD=...
CA_PATH=/usr/local/share/ca-certificates/ca.crt
QUEUE_CONTROL_TOPIC=queue-control
QUEUE_EVENTS_TOPIC=queue-events

# ArangoDB
ARANGO_URL=http://abase-3.dmz.home:8529
ARANGO_DB=streamforge
ARANGO_USER=root
ARANGO_PASSWORD=...

# Очередь (runtime)
QUEUE_ID=...
SYMBOL=BTCUSDT
TYPE=api_candles_5m
INTERVAL=5m
TIME_RANGE=2024-06-01:2024-06-02
KAFKA_TOPIC=...

# Телеметрия
TELEMETRY_PRODUCER_ID=...

# Docker images
LOADER_IMAGE=...
CONSUMER_IMAGE=...
GNN_TRAINER_IMAGE=...
VISUALIZER_IMAGE=...
```




