# [Orchestrator] StreamForge Queue Manager

**Queue Manager** — это центральный оркестрационный сервис платформы **StreamForge**, спроектированный для управления жизненным циклом сложных, событийно-ориентированных конвейеров обработки данных. Он выступает в роли единой точки входа для запуска, мониторинга и остановки всех ETL и ML процессов в системе.

---

## 🎯 Core Responsibilities

- **Pipeline Orchestration**: Динамический запуск и координация цепочек микросервисов (`loader`, `connector`, `graph-builder`, `gnn-trainer`) в виде заданий Kubernetes.
- **Lifecycle Management**: Управление полным жизненным циклом очередей обработки, от инициации до завершения или принудительной остановки.
- **State Persistence**: Сохранение метаданных и конфигураций запущенных конвейеров в **ArangoDB** для обеспечения отслеживаемости и возможности последующего анализа.
- **Dynamic ID Generation**: Автоматическая генерация стандартизированных идентификаторов (`queue_id`, `kafka_topic`, `collection_name`) для всех компонентов системы, что обеспечивает предсказуемость и упрощает отладку.
- **Asynchronous Control**: Взаимодействие с микросервисами через брокер сообщений **Kafka** для отправки команд (`queue-control`) и приема телеметрии (`queue-events`).

---

## 🏛️ Architecture

Сервис построен на базе **FastAPI**, что обеспечивает высокую производительность и автоматическую генерацию интерактивной документации API (Swagger).

- **API Layer**: Предоставляет RESTful API для управления конвейерами.
- **Orchestration Logic**: Транслирует API-запросы в конкретные действия: генерация имен, формирование переменных окружения и запуск заданий в **Kubernetes** через клиент `python-kubernetes`.
- **State Layer**: Взаимодействует с **ArangoDB** для сохранения и извлечения информации о запущенных очередях.
- **Communication Layer**: Интегрируется с **Kafka** для асинхронного обмена командами и событиями с другими микросервисами.

---

## ⚙️ API Endpoints (Swagger)

Основной и наиболее мощный эндпоинт системы — `/queues/start-pipeline`. Он позволяет запустить сложный конвейер, состоящий из нескольких взаимосвязанных микросервисов, одним запросом.

### `POST /queues/start-pipeline`

Этот эндпоинт принимает объект `QueueStartRequest`, который описывает общие параметры конвейера (например, `symbol`) и содержит список `microservices` для последовательного запуска.

#### Модель запроса: `QueueStartRequest`

```json
{
  "symbol": "BTCUSDT",
  "time_range": "2024-06-01:2024-06-30",
  "microservices": [
    {
      "target": "loader-producer",
      "type": "api_candles_5m",
      "interval": "5m"
    },
    {
      "target": "arango-connector",
      "type": "api_candles_5m"
    }
  ]
}
```

- `symbol` (`string`, **required**): Торговый символ (например, `BTCUSDT`).
- `time_range` (`string`, optional): Временной диапазон для загрузки исторических данных.
- `microservices` (`list[MicroserviceConfig]`, **required**): Список конфигураций микросервисов для запуска.

#### Модель `MicroserviceConfig`

- `target` (`string`, **required**): Имя целевого микросервиса. Допустимые значения: `loader-producer`, `arango-connector`, `graph-builder`, `gnn-trainer`, `visualizer`, и др.
- `type` (`string`, **required**): Тип задачи, определяющий логику работы микросервиса (например, `api_candles_5m`, `ws_trades`, `gnn_graph`).
- `image` (`string`, optional): Позволяет переопределить Docker-образ для конкретного задания.
- `...прочие_поля`: Дополнительные параметры, специфичные для каждого микросервиса (`collection_inputs`, `model_output` и т.д.).

---

### 💡 Примеры запросов

#### Пример 1: Конвейер для обучения GNN на исторических данных

Этот запрос запускает полную цепочку: загрузка свечей и сделок, сохранение их в ArangoDB, построение графа и запуск обучения GNN-модели.

```json
{
  "symbol": "ETHUSDT",
  "time_range": "2024-07-01:2024-07-31",
  "microservices": [
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
        "eth_candles_5m_2024_07",
        "eth_trades_2024_07"
      ],
      "collection_output": "eth_graph_2024_07"
    },
    {
      "target": "gnn-trainer",
      "type": "gnn_train",
      "graph_collection": "eth_graph_2024_07",
      "model_output": "gnn_model_eth_2024_07"
    }
  ]
}
```
**Анализ запроса:**
- Запускается 6 заданий в Kubernetes.
- `loader-producer` и `arango-connector` работают с общим `kafka_topic`, сгенерированным на основе `symbol` и `type` первого элемента (`api_candles_5m`).
- `graph-builder` использует `collection_inputs` для указания исходных коллекций и `collection_output` для результата.
- `gnn-trainer` получает на вход граф из `graph_collection` и сохраняет обученную модель под именем `model_output`.

#### Пример 2: Конвейер для real-time визуализации данных

Этот запрос запускает загрузку данных по WebSocket и их отображение.

```json
{
  "symbol": "BTCUSDT",
  "time_range": null,
  "microservices": [
    {
      "target": "loader-ws",
      "type": "ws_trades"
    },
    {
      "target": "arango-connector",
      "type": "ws_trades"
    },
    {
      "target": "visualizer",
      "type": "graph_metrics_stream",
      "source": "btc_ws_trades_realtime"
    }
  ]
}
```
**Анализ запроса:**
- `time_range` установлен в `null`, так как данные поступают в реальном времени.
- Запускаются сервисы для получения (`loader-ws`), сохранения (`arango-connector`) и визуализации (`visualizer`) данных.
- `visualizer` использует параметр `source` для подписки на нужный поток данных.

---

## 🏷️ Генерация имен и ID

На основе одного запроса `queue-manager` автоматически генерирует стандартизированные идентификаторы для всех ресурсов, обеспечивая их уникальность и предсказуемость.

**Входные данные:**
- `symbol`: `BTCUSDT`
- `type`: `api_candles_1h`
- `time_range`: `2024-08-01:2024-08-02`

**Сгенерированные ресурсы:**
- `short_id`: `jLd4fG` (уникальный идентификатор)
- `queue_id`: `loader-btcusdt-api-candles-1h-2024-08-01-jLd4fG`
- `kafka_topic`: `loader-btcusdt-api-candles-1h-2024-08-01-jLd4fG`
- `collection_name`: `btc_candles_1h_2024_08_01`
- `telemetry_id` (для `loader-producer`): `loader-producer__jLd4fG`

---

## 📡 Асинхронное взаимодействие (Kafka)

- **`queue-events` (Topic)**: Все микросервисы отправляют в этот топик события о своем состоянии (старт, прогресс, завершение, ошибка), что позволяет `queue-manager` (и другим системам) отслеживать статус выполнения в реальном времени.
- **`queue-control` (Topic)**: `queue-manager` отправляет в этот топик команды, например, на остановку. Микросервисы подписываются на него и корректно завершают свою работу при получении команды, адресованной их `queue_id`.
