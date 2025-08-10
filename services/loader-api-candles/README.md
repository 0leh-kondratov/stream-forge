# 🕯️ loader-api-candles

Микросервис в экосистеме **StreamForge**, предназначенный для загрузки исторических данных свечей через REST API и публикации их в Kafka.

## 🎯 Назначение

`loader-api-candles` выполняет следующие задачи:

1.  **Подключается** к внешнему API (например, Binance).
2.  **Загружает** исторические данные свечей для указанной торговой пары и интервала.
3.  **Публикует** полученные данные в Kafka-топик.

Этот сервис является stateless-воркером и предназначен для запуска в виде **Kubernetes Job**. Всю необходимую конфигурацию он получает через переменные окружения.

## ⚙️ Переменные окружения

Сервис полностью настраивается через переменные окружения.

| Переменная                 | Описание                                                              | Пример                                           |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| **`QUEUE_ID`**             | Уникальный идентификатор всего workflow.                              | `wf-candles-load-20240801-a1b2c3`                 |
| **`SYMBOL`**               | Торговая пара для загрузки данных.                                    | `BTCUSDT`                                        |
| **`TYPE`**                 | Тип данных, который обрабатывается.                                   | `api_candles`                                    |
| **`KAFKA_TOPIC`**          | Имя Kafka-топика, куда публиковать данные.                             | `wf-candles-load-20240801-a1b2c3-data`           |
| **`TIME_RANGE`**           | Диапазон времени для загрузки данных (START_DATE:END_DATE).           | `2023-01-01:2023-01-02`                          |
| **`INTERVAL`**             | Интервал свечей (например, `1m`, `1h`, `1d`).                         | `1h`                                             |
| **`TELEMETRY_PRODUCER_ID`**| Уникальный ID этого экземпляра для телеметрии.                        | `loader-api-candles__a1b2c3`                     |
| `KAFKA_BOOTSTRAP_SERVERS`  | Адреса брокеров Kafka.                                                | `kafka-bootstrap.kafka:9093`                     |
| `KAFKA_USER_PRODUCER`      | Имя пользователя для аутентификации в Kafka (producer).               | `user-producer-tls`                              |
| `KAFKA_PASSWORD_PRODUCER`  | Пароль для пользователя Kafka (передается через Secret).              | `your_kafka_password`                            |
| `CA_PATH`                  | Путь к CA-сертификату для TLS-соединения с Kafka.                     | `/certs/ca.crt`                                  |
| `QUEUE_CONTROL_TOPIC`      | Топик для получения управляющих команд (например, `stop`).            | `queue-control`                                  |
| `QUEUE_EVENTS_TOPIC`       | Топик для отправки событий телеметрии.                                | `queue-events`                                   |
| `BINANCE_API_KEY`          | API ключ для доступа к Binance API.                                   | `your_binance_api_key`                           |
| `BINANCE_API_SECRET`       | API секрет для доступа к Binance API.                                 | `your_binance_api_secret`                        |

---

## 📥 Входные данные (API)

Сервис подключается к внешнему API (например, Binance) для получения данных свечей. Формат данных соответствует стандартному формату K-lines.

---

## 📤 Выходные данные (Kafka)

Сервис публикует полученные данные свечей в топик `KAFKA_TOPIC` в формате JSON. Каждое сообщение представляет собой одну свечу.

```json
{
  "open_time": 1672531200000,
  "open": 16541.23,
  "high": 16542.88,
  "low": 16540.99,
  "close": 16541.98,
  "volume": 123.45,
  "close_time": 1672531259999,
  "quote_asset_volume": 2042134.56,
  "number_of_trades": 456,
  "taker_buy_base_asset_volume": 60.12,
  "taker_buy_quote_asset_volume": 994512.34,
  "symbol": "BTCUSDT",
  "interval": "1h"
}
```

---

## 📡 Телеметрия (Topic: `queue-events`)

Сервис отправляет события о своем состоянии в топик `queue-events`. Это позволяет `queue-manager` отслеживать прогресс выполнения задачи.

**Пример события `loading`:**

```json
{
  "queue_id": "wf-candles-load-20240801-a1b2c3",
  "symbol": "BTCUSDT",
  "type": "api_candles",
  "status": "loading",
  "message": "Загружено и опубликовано 15000 записей свечей",
  "records_written": 15000,
  "finished": false,
  "producer": "loader-api-candles__a1b2c3",
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
  "queue_id": "wf-candles-load-20240801-a1b2c3"
}
```

При получении этой команды сервис корректно завершает свою работу.
