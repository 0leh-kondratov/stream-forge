# 🔥 arango-candles

Микросервис-консьюмер в экосистеме **StreamForge**.

## 🎯 Назначение

`arango-candles` выполняет одну задачу:

1.  **Слушает** определенный топик в Kafka, в который поступают данные по свечам (`candles`).
2.  **Обрабатывает** эти сообщения пачками (батчами).
3.  **Сохраняет** их в соответствующую коллекцию в базе данных ArangoDB.

Этот сервис является stateless-воркером и предназначен для запуска в виде **Kubernetes Job**. Всю необходимую конфигурацию он получает через переменные окружения.

## ⚙️ Переменные окружения

Сервис полностью настраивается через переменные окружения.

| Переменная                 | Описание                                                              | Пример                                           |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| **`QUEUE_ID`**             | Уникальный идентификатор всего workflow.                              | `wf-btcusdt-20240801-a1b2c3`                      |
| **`SYMBOL`**               | Торговая пара.                                                        | `BTCUSDT`                                        |
| **`TYPE`**                 | Тип данных, который обрабатывается.                                   | `api_candles_1m`                                 |
| **`KAFKA_TOPIC`**          | Имя Kafka-топика, из которого читать данные.                           | `wf-btcusdt-20240801-a1b2c3-api-candles-1m`       |
| **`COLLECTION_NAME`**      | Имя коллекции в ArangoDB для сохранения данных.                       | `btcusdt_api_candles_1m_2024_08_01`                |
| **`TELEMETRY_PRODUCER_ID`**| Уникальный ID этого экземпляра для телеметрии.                        | `arango-candles__a1b2c3`                         |
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

Сервис ожидает получать из топика `KAFKA_TOPIC` JSON-сообщения следующего формата:

```json
{
  "_key": "BTCUSDT_1m_1672531200000",
  "open_time": 1672531200000,
  "open": "16541.23",
  "high": "16542.88",
  "low": "16540.99",
  "close": "16541.98",
  "volume": "123.45",
  "close_time": 1672531259999,
  "quote_asset_volume": "2042134.56",
  "number_of_trades": 456,
  "taker_buy_base_asset_volume": "60.12",
  "taker_buy_quote_asset_volume": "994512.34"
}
```

Поле `_key` используется для идемпотентной вставки/обновления данных в ArangoDB (`UPSERT`).

---

## 📡 Телеметрия (Topic: `queue-events`)

Сервис отправляет события о своем состоянии в топик `queue-events`. Это позволяет `queue-manager` отслеживать прогресс выполнения задачи.

**Пример события `loading`:**

```json
{
  "queue_id": "wf-btcusdt-20240801-a1b2c3",
  "symbol": "BTCUSDT",
  "type": "api_candles_1m",
  "status": "loading",
  "message": "Сохранено 15000 записей",
  "records_written": 15000,
  "finished": false,
  "producer": "arango-candles__a1b2c3",
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
  "queue_id": "wf-btcusdt-20240801-a1b2c3"
}
```

При получении этой команды сервис корректно завершает свою работу: останавливает консьюмер, закрывает соединение с БД и отправляет финальное событие телеметрии со статусом `interrupted`.

