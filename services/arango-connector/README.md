# 🔗 arango-connector

Микросервис-консьюмер в экосистеме **StreamForge**, предназначенный для универсальной персистентности данных в ArangoDB.

## 🎯 Назначение

`arango-connector` выполняет следующие задачи:

1.  **Слушает** определенный топик в Kafka, в который поступают данные.
2.  **Обрабатывает** эти сообщения.
3.  **Сохраняет** их в соответствующую коллекцию в базе данных ArangoDB.

Этот сервис является stateless-воркером и предназначен для запуска в виде **Kubernetes Job**. Всю необходимую конфигурацию он получает через переменные окружения.

## ⚙️ Переменные окружения

Сервис полностью настраивается через переменные окружения.

| Переменная                 | Описание                                                              | Пример                                           |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| **`QUEUE_ID`**             | Уникальный идентификатор всего workflow.                              | `wf-generic-data-20240801-a1b2c3`                 |
| **`SYMBOL`**               | Символ или идентификатор данных.                                      | `GENERIC_DATA`                                   |
| **`TYPE`**                 | Тип данных, который обрабатывается.                                   | `raw_json`                                       |
| **`KAFKA_TOPIC`**          | Имя Kafka-топика, из которого читать данные.                           | `wf-generic-data-20240801-a1b2c3-raw`             |
| **`COLLECTION_NAME`**      | Имя коллекции в ArangoDB для сохранения данных.                       | `generic_data_2024_08_01`                        |
| **`TELEMETRY_PRODUCER_ID`**| Уникальный ID этого экземпляра для телеметрии.                        | `arango-connector__a1b2c3`                       |
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

Сервис ожидает получать из топика `KAFKA_TOPIC` JSON-сообщения. Предполагается, что сообщения могут содержать поле `_key` для идемпотентной вставки/обновления данных в ArangoDB (`UPSERT`). Если `_key` отсутствует, ArangoDB сгенерирует его автоматически.

```json
{
  "_key": "unique_document_id",
  "field1": "value1",
  "field2": "value2",
  "timestamp": 1722500000.123
}
```

---

## 📡 Телеметрия (Topic: `queue-events`)

Сервис отправляет события о своем состоянии в топик `queue-events`. Это позволяет `queue-manager` отслеживать прогресс выполнения задачи.

**Пример события `loading`:**

```json
{
  "queue_id": "wf-generic-data-20240801-a1b2c3",
  "symbol": "GENERIC_DATA",
  "type": "raw_json",
  "status": "loading",
  "message": "Сохранено 15000 записей",
  "records_written": 15000,
  "finished": false,
  "producer": "arango-connector__a1b2c3",
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
  "queue_id": "wf-generic-data-20240801-a1b2c3"
}
```

При получении этой команды сервис корректно завершает свою работу: останавливает консьюмер, закрывает соединение с БД и отправляет финальное событие телеметрии со статусом `interrupted`.
