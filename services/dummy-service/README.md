
# 🧠 `dummy-service`: Telemetry & Command Simulation Microservice

`dummy-service` — это тестовый микросервис StreamForge, предназначенный для:

* получения команд из Kafka (`queue-control`);
* отправки событий (`started`, `pong`, `interrupted`, `finished`) в Kafka (`queue-events`);
* имитации загрузки и ошибок;
* логирования в формате structured JSON;
* публикации Prometheus-метрик через HTTP (`/metrics`);
* запуска в Kubernetes как `Job`, `Pod`, `Deployment` или локально.

---

## 🚀 Основные функции

| Функция            | Описание                                                      |
| ------------------ | ------------------------------------------------------------- |
| `ping/pong`        | Реакция на `ping` команду, отправка `pong` с меткой времени   |
| `stop`             | Завершение по команде с публикацией `interrupted` события     |
| `simulate-loading` | Периодическая отправка `loading` событий в Kafka              |
| `fail-after N`     | Принудительная отправка `error` и завершение через `N` секунд |
| `/metrics`         | Экспорт Prometheus-метрик (счётчики событий, статус)          |
| JSON-логирование   | Структурированные логи, совместимые с Fluent Bit / Loki       |

---

## 🧾 Переменные окружения

| Переменная                | Назначение                                      |
| ------------------------- | ----------------------------------------------- |
| `QUEUE_ID`                | Уникальный ID очереди (например, loader-...)    |
| `SYMBOL`                  | Тикер, например `BTCUSDT`                       |
| `TIME_RANGE`              | Диапазон, например `2024-01-01:2024-01-02`      |
| `TYPE`                    | Тип источника: `api`, `ws`, `dummy`, ...        |
| `TELEMETRY_PRODUCER_ID`   | Идентификатор сервиса в событиях                |
| `KAFKA_TOPIC`             | Целевой Kafka-топик                             |
| `QUEUE_EVENTS_TOPIC`      | Kafka topic для событий (обычно `queue-events`) |
| `QUEUE_CONTROL_TOPIC`     | Kafka topic для команд (обычно `queue-control`) |
| `KAFKA_BOOTSTRAP_SERVERS` | Адрес брокера Kafka                             |
| `KAFKA_USER`              | SCRAM-пользователь                              |
| `KAFKA_PASSWORD`          | SCRAM-пароль                                    |
| `KAFKA_CA_PATH`           | Путь к CA-файлу для TLS                         |
| `ARANGO_*`                | Данные подключения к ArangoDB (опционально)     |

---

## 🏁 Пример запуска (локально)

Для запуска `dummy-service` локально (например, внутри `devcontainer`), сначала перейдите в директорию сервиса, а затем используйте флаг `-m` для запуска как модуля:

```bash
cd /data/projects/stream-forge/services/dummy-service/
python3.11 -m app.main \
  --debug \
  --simulate-loading \
  --exit-after 30
```

---

## 🧪 Тестирование через `debug_producer.py`

`debug_producer.py` — это CLI-инструмент для отправки тестовых команд в Kafka-топик `queue-control` и ожидания ответов из `queue-events`. Он используется для отладки и тестирования микросервисов, взаимодействующих через Kafka.

### Примеры использования:

*   **Тестирование связности Kafka (ping/pong):**
    Отправьте команду `ping` и ожидайте `pong` для проверки базовой связности и работоспособности целевого микросервиса.
    ```bash
    python3.11 debug_producer.py \
      --queue-id <ваш-queue-id> \
      --command ping \
      --expect-pong
    ```

*   **Тестирование команды остановки (stop):**
    Отправьте сигнал `stop` целевому сервису, который должен корректно завершить свою работу.
    ```bash
    python3.11 debug_producer.py \
      --queue-id <ваш-queue-id> \
      --command stop
    ```



---

## 🧩 Поддерживаемые флаги `main.py`

| Флаг                 | Назначение                                                |
| -------------------- | --------------------------------------------------------- |
| `--debug`            | Включает DEBUG уровень логов                              |
| `--noop`             | Только отправка `started`, без запуска Kafka consumer     |
| `--exit-on-ping`     | Завершает работу после получения `ping` и отправки `pong` |
| `--exit-after N`     | Завершает через `N` секунд                                |
| `--simulate-loading` | Каждые 10 секунд отправляет `loading`                     |
| `--fail-after N`     | Генерирует `error` и завершает работу через `N` секунд    |

---

## 📊 Метрики (`/metrics`)

Доступны по порту `8000`, включают:

* `dummy_events_total{event="started|pong|interrupted|..."}`
* `dummy_pings_total`, `dummy_pongs_total`
* `dummy_status_last{status="loading|interrupted|finished"}`

---

## 🐳 Пример `Dockerfile` запуска

```dockerfile
CMD ["python3.11", "main.py", "--simulate-loading", "--exit-after", "30"]
```

---

## ☸️ Kubernetes Integration

Рекомендуется запуск как `Job` или `Pod` с:

* `envFrom`: ConfigMap + Secret
* Volume для CA (`/usr/local/share/ca-certificates/ca.crt`)
* Подключение к Kafka через TLS + SCRAM

---

## 📂 Использование в StreamForge

`dummy-service` может использоваться как:

* 🔄 эмулятор загрузчика (`loader`)
* 📡 проверка связности Kafka (`ping/pong`)
* 🎯 CI/CD тест команд `stop`, `interrupted`
* 🔍 мониторинг метрик и логов в реальном времени

---

