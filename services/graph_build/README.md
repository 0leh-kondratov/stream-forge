# 🏗️ graph-build

Микросервис в экосистеме **StreamForge**, предназначенный для построения графовых структур из подготовленных данных и их сохранения в ArangoDB.

## 🎯 Назначение

`graph-build` выполняет следующие задачи:

1.  **Слушает** определенный топик в Kafka, в который поступают подготовленные данные для графа.
2.  **Обрабатывает** эти сообщения, извлекая узлы и ребра.
3.  **Строит** графовые структуры и **сохраняет** их в соответствующие коллекции в базе данных ArangoDB.

Этот сервис является stateless-воркером и предназначен для запуска в виде **Kubernetes Job**. Всю необходимую конфигурацию он получает через переменные окружения.

## ⚙️ Переменные окружения

Сервис полностью настраивается через переменные окружения.

| Переменная                 | Описание                                                              | Пример                                           |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| **`QUEUE_ID`**             | Уникальный идентификатор всего workflow.                              | `wf-graph-build-20240801-a1b2c3`                  |
| **`SYMBOL`**               | Символ или идентификатор данных.                                      | `GRAPH_STRUCTURE`                                |
| **`TYPE`**                 | Тип данных, который обрабатывается.                                   | `graph_data`                                     |
| **`KAFKA_TOPIC`**          | Имя Kafka-топика, из которого читать подготовленные данные.            | `wf-graph-build-20240801-a1b2c3-prepared`         |
| **`GRAPH_COLLECTION_NAME`**| Имя коллекции в ArangoDB для сохранения графовых данных.              | `market_graph_2024_08_01`                        |
| **`TELEMETRY_PRODUCER_ID`**| Уникальный ID этого экземпляра для телеметрии.                        | `graph-build__a1b2c3`                            |
| `KAFKA_BOOTSTRAP_SERVERS`  | Адреса брокеров Kafka.                                                | `kafka-bootstrap.kafka:9093`                     |
| `KAFKA_USER_CONSUMER`      | Имя пользователя для аутентификации в Kafka (consumer).               | `user-consumer-tls`                              |
| `KAFKA_PASSWORD_CONSUMER`  | Пароль для пользователя Kafka (передается через Secret).              | `your_kafka_password`                            |
| `CA_PATH`                  | Путь к CA-сертификату для TLS-соединения с Kafka.                     | `/certs/ca.crt`                                  |
| `QUEUE_CONTROL_TOPIC`      | Топик для получения управляющих команд (например, `stop`).            | `queue-control`                                  |
| `QUEUE_EVENTS_TOPIC`       | Топик для отправки событий телеметрии.                                | `queue-events`                                   |
| `ARANGO_URL`               | URL для подключения к ArangoDB.                                       | `http://arango-cluster.db:8529`                  |
| `ARANGO_DB`                | Имя базы данных в ArangoDB.                                           | `streamforge`                                    |
| `ARANGO_USER`              | Пользователь для подключения к ArangoDB.                              | `root`                                           |
| `ARANGO_PASSWORD`          | Пароль для ArangoDB (передается через Secret).                        | `your_arango_password`                           |

---

## 📥 Входные данные (Kafka)

Сервис ожидает получать из топика `KAFKA_TOPIC` JSON-сообщения, представляющие собой подготовленные данные для построения графа. Предполагается, что сообщения могут содержать поле `_key` для идемпотентной вставки/обновления данных в ArangoDB (`UPSERT`). Если `_key` отсутствует, ArangoDB сгенерирует его автоматически.

```json
{
  "_key": "node_id_1",
  "type": "node",
  "attributes": {"feature1": 1.0, "feature2": "value"}
}
```

---

## 📡 Телеметрия (Topic: `queue-events`)

Сервис отправляет события о своем состоянии в топик `queue-events`. Это позволяет `queue-manager` отслеживать прогресс выполнения задачи.

**Пример события `loading`:**

```json
{
  "queue_id": "wf-graph-build-20240801-a1b2c3",
  "symbol": "GRAPH_STRUCTURE",
  "type": "graph_data",
  "status": "loading",
  "message": "Построено 15000 узлов и ребер",
  "records_written": 15000,
  "finished": false,
  "producer": "graph-build__a1b2c3",
  "timestamp": 1722445567.890
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
  "queue_id": "wf-graph-build-20240801-a1b2c3"
}
```

При получении этой команды сервис корректно завершает свою работу.
