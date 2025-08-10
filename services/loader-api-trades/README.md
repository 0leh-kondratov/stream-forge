# 📈 loader-api-trades

Микросервис в экосистеме **StreamForge**, предназначенный для загрузки исторических данных о торговых сделках через REST API и публикации их в Kafka.

## 🎯 Назначение

`loader-api-trades` выполняет следующие задачи:

1.  **Подключается** к внешнему API (например, Binance).
2.  **Загружает** исторические данные о сделках для указанной торговой пары.
3.  **Публикует** полученные данные в Kafka-топик.

Этот сервис является stateless-воркером и предназначен для запуска в виде **Kubernetes Job**. Всю необходимую конфигурацию он получает через переменные окружения.

## ⚙️ Переменные окружения

Сервис полностью настраивается через переменные окружения.

| Переменная                 | Описание                                                              | Пример                                           |
| -------------------------- | --------------------------------------------------------------------- | ------------------------------------------------ |
| **`QUEUE_ID`**             | Уникальный идентификатор всего workflow.                              | `wf-trades-load-20240801-a1b2c3`                  |
| **`SYMBOL`**               | Торговая пара для загрузки данных.                                    | `BTCUSDT`                                        |
| **`TYPE`**                 | Тип данных, который обрабатывается.                                   | `api_trades`                                     |
| **`KAFKA_TOPIC`**          | Имя Kafka-топика, куда публиковать данные.                             | `wf-trades-load-20240801-a1b2c3-data`            |
| **`TIME_RANGE`**           | Диапазон времени для загрузки данных (START_DATE:END_DATE).           | `2023-01-01:2023-01-02`                          |
| **`LIMIT`**                | Максимальное количество сделок за один запрос.                        | `1000`                                           |
| **`TELEMETRY_PRODUCER_ID`**| Уникальный ID этого экземпляра для телеметрии.                        | `loader-api-trades__a1b2c3`                      |
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

Сервис подключается к внешнему API (например, Binance) для получения данных о сделках. Формат данных соответствует агрегированным сделкам Binance (`aggTrades`).

---

## 📤 Выходные данные (Kafka)

Сервис публикует полученные данные о сделках в топик `KAFKA_TOPIC` в формате JSON. Каждое сообщение представляет собой одну сделку.

```json
{
  "trade_id": 12345,
  "price": 20000.50,
  "quantity": 0.1,
  "timestamp": 1672531200000,
  "is_buyer_maker": true,
  "symbol": "BTCUSDT"
}
```

---

## 📡 Телеметрия (Topic: `queue-events`)

Сервис отправляет события о своем состоянии в топик `queue-events`. Это позволяет `queue-manager` отслеживать прогресс выполнения задачи.

**Пример события `loading`:**

```json
{
  "queue_id": "wf-trades-load-20240801-a1b2c3",
  "symbol": "BTCUSDT",
  "type": "api_trades",
  "status": "loading",
  "message": "Загружено и опубликовано 15000 записей сделок",
  "records_written": 15000,
  "finished": false,
  "producer": "loader-api-trades__a1b2c3",
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
  "queue_id": "wf-trades-load-20240801-a1b2c3"
}
```

При получении этой команды сервис корректно завершает свою работу.
