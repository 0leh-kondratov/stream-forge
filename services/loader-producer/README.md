# 📦 loader-producer

Микросервис в экосистеме **StreamForge**, предназначенный для высокопроизводительной массовой загрузки данных и публикации их в Kafka.

## 🎯 Назначение

`loader-producer` выполняет следующие задачи:

1.  **Подключается** к источнику данных (например, Binance API).
2.  **Загружает** данные (например, исторические свечи, сделки).
3.  **Публикует** полученные данные в Kafka-топик.

Этот сервис является stateless-воркером и предназначен для запуска в виде **Kubernetes Job**. Всю необходимую конфигурацию он получает через переменные окружения.

## ⚙️ Переменные окружения

Сервис полностью настраивается через переменные окружения.

| Переменная                 | Описание                                                              | Пример                                           |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| **`QUEUE_ID`**             | Уникальный идентификатор всего workflow.                              | `wf-bulk-load-20240801-a1b2c3`                    |
| **`SYMBOL`**               | Торговая пара или идентификатор данных.                               | `BTCUSDT`                                        |
| **`TYPE`**                 | Тип данных, который обрабатывается (например, `api_candles_1m`, `ws_trades`). | `api_candles_1m`                                 |
| **`TIME_RANGE`**           | Диапазон времени для загрузки данных (START_DATE:END_DATE).           | `2023-01-01:2023-01-02`                          |
| **`INTERVAL`**             | Интервал свечей (для `api_candles`, `ws_candles`).                    | `1h`                                             |
| **`KAFKA_TOPIC`**          | Имя Kafka-топика, куда публиковать данные.                             | `wf-bulk-load-20240801-a1b2c3-data`              |
| **`TELEMETRY_PRODUCER_ID`**| Уникальный ID этого экземпляра для телеметрии.                        | `loader-producer__a1b2c3`                        |
| `KAFKA_BOOTSTRAP_SERVERS`  | Адреса брокеров Kafka.                                                | `kafka-bootstrap.kafka:9093`                     |
| `KAFKA_USER_PRODUCER`      | Имя пользователя для аутентификации в Kafka (producer).               | `user-producer-tls`                              |
| `KAFKA_PASSWORD_PRODUCER`  | Пароль для пользователя Kafka (передается через Secret).              | `your_kafka_password`                            |
| `CA_PATH`                  | Путь к CA-сертификату для TLS-соединения с Kafka.                     | `/certs/ca.crt`                                  |
| `QUEUE_CONTROL_TOPIC`      | Топик для получения управляющих команд (например, `stop`).            | `queue-control`                                  |
| `QUEUE_EVENTS_TOPIC`       | Топик для отправки событий телеметрии.                                | `queue-events`                                   |
| `BINANCE_API_URL`          | Базовый URL для Binance REST API.                                     | `https://api.binance.com`                        |
| `BINANCE_WS_URL`           | Базовый URL для Binance WebSocket API.                                | `wss://stream.binance.com:9443/ws`               |
| `BINANCE_API_KEY`          | API ключ для доступа к Binance API.                                   | `your_binance_api_key`                           |
| `BINANCE_API_SECRET`       | API секрет для доступа к Binance API.                                 | `your_binance_api_secret`                        |
| `TELEMETRY_INTERVAL`       | Интервал отправки телеметрии (в секундах).                             | `5`                                              |
| `DEBUG`                    | Включить отладочный режим.                                            | `true`                                           |

---

## 📥 Входные данные (API/WS)

Сервис подключается к внешним источникам данных (например, Binance API/WS) для получения данных. Формат данных зависит от `TYPE`.

---

## 📤 Выходные данные (Kafka)

Сервис публикует полученные данные в топик `KAFKA_TOPIC` в формате JSON. Каждое сообщение представляет собой одну запись данных.

---

## 📡 Телеметрия (Topic: `queue-events`)

Сервис отправляет события о своем состоянии в топик `queue-events`. Это позволяет `queue-manager` отслеживать прогресс выполнения задачи.

**Пример события `loading`:**

```json
{
  "queue_id": "wf-bulk-load-20240801-a1b2c3",
  "symbol": "BTCUSDT",
  "type": "api_candles_1m",
  "status": "loading",
  "message": "Загружено и опубликовано 15000 записей",
  "records_written": 15000,
  "finished": false,
  "producer": "loader-producer__a1b2c3",
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
  "queue_id": "wf-bulk-load-20240801-a1b2c3"
}
```

При получении этой команды сервис корректно завершает свою работу.
