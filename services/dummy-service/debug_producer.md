
# 🧪 `debug_producer.py`: Kafka Command Tester for StreamForge

`debug_producer.py` — это CLI-инструмент для отправки тестовых команд (`ping`, `stop`) в Kafka-топик `queue-control`, с возможностью ожидания ответа `pong` из `queue-events`.

Используется для отладки микросервисов StreamForge, в первую очередь — `dummy-service`, `loader-producer`, `arango-connector`.

---

## ⚙️ Основные возможности

* Отправка команды `ping` с ожиданием `pong`
* Отправка команды `stop`
* Повторная отправка `ping` (режим `--repeat`)
* Подсчёт RTT (время между `ping_ts` и `ponged_at`)
* JSON-логирование отправленных и полученных событий

---

## 📥 Аргументы командной строки

| Аргумент        | Тип         | Описание                                                             |                                  |
| --------------- | ----------- | -------------------------------------------------------------------- | -------------------------------- |
| `--queue-id`    | str (обяз.) | Идентификатор целевой очереди (например: `loader-btcusdt-dummy-...`) |                                  |
| `--command`     | \`ping      | stop\`                                                               | Команда, которую нужно отправить |
| `--expect-pong` | флаг        | Ожидать `pong` после `ping`, логировать задержку                     |                                  |
| `--repeat`      | int         | Повторить команду `N` раз                                            |                                  |
| `--interval`    | float       | Интервал между повторами (в секундах, по умолчанию `1.0`)            |                                  |

---

## 🔧 Требуемые переменные окружения

`debug_producer.py` использует Kafka через SASL + TLS. Настрой как `.env` или `export`:

```dotenv
KAFKA_BOOTSTRAP_SERVERS=k3-kafka-bootstrap.kafka:9093
KAFKA_USER=user-streamforge
KAFKA_PASSWORD=topsecret
KAFKA_CA_PATH=/usr/local/share/ca-certificates/ca.crt

QUEUE_CONTROL_TOPIC=queue-control
QUEUE_EVENTS_TOPIC=queue-events
```

---

## 🚀 Примеры использования

### ✅ Отправить один `ping` и дождаться `pong`

```bash
python3.11 debug_producer.py \
  --queue-id loader-btcusdt-dummy-2024-06-01-testid \
  --command ping \
  --expect-pong
```

---

### ✅ Отправить 5 `ping` с интервалом 2 секунды

```bash
python3.11 debug_producer.py \
  --queue-id loader-btcusdt-dummy-2024-06-01-testid \
  --command ping \
  --expect-pong \
  --repeat 5 \
  --interval 2
```

---

### ✅ Отправить `stop` и завершить очередь

```bash
python3.11 debug_producer.py \
  --queue-id loader-btcusdt-dummy-2024-06-01-testid \
  --command stop
```

---

## 📊 Формат событий в Kafka

### 📤 Отправляется:

```json
{
  "queue_id": "loader-btcusdt-dummy-2024-06-01-testid",
  "command": "ping",
  "sent_at": 1754202651.997
}
```

### 📥 Ожидается (от `dummy-service`):

```json
{
  "event": "pong",
  "queue_id": "loader-btcusdt-dummy-2024-06-01-testid",
  "ping_ts": 1754202651.997,
  "ponged_at": 1754202652.045
}
```

---

## 🧠 Дополнительно

* RTT (Round-Trip Time) рассчитывается как `ponged_at - ping_ts`
* Утилита может использоваться для CI-тестов
* Встроенный Kafka consumer автоматически отключается после `pong`

---

## 📁 Рекомендации

* Использовать внутри кластера Kubernetes как `Job` для диагностики
* Применять в GitLab CI для проверки доступности Kafka и очередей
* Подходит для наблюдения за `queue-events` и тестирования `loader`/`connector`

---
