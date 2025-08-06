## Часть V: Технические детали для любопытных

### Приложение А: Схемы данных и API

(Здесь будут все технические спецификации API для `queue-manager` и подробные JSON-схемы для сообщений Kafka. Это для тех, кто любит копаться в деталях!)

### Приложение Б: Примеры манифестов Kubernetes

#### Пример: Kubernetes Job для `arango-candles`

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: job-arango-candles-btcusdt-abc123
  namespace: stf
  labels:
    app: streamforge
    queue_id: "wf-btcusdt-api_candles_1m-20240801-abc123"
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: arango-candles
          image: registry.dmz.home/streamforge/arango-candles:v0.1.5
          env:
            - name: QUEUE_ID
              value: "wf-btcusdt-api_candles_1m-20240801-abc123"
            - name: SYMBOL
              value: "BTCUSDT"
            - name: TYPE
              value: "api_candles_1m"
            - name: KAFKA_TOPIC
              value: "wf-btcusdt-api_candles_1m-20240801-abc123-data"
            - name: COLLECTION_NAME
              value: "btcusdt_api_candles_1m_2024_08_01"
            # ... прочие переменные из ConfigMap и Secret ...
      nodeSelector:
        streamforge-worker: "true" # Пример селектора для выделенных нод
  backoffLimit: 2
  ttlSecondsAfterFinished: 3600
```

### Приложение В: Примеры CI/CD пайплайнов

(Здесь будут полные `.gitlab-ci.yml` файлы для каждого микросервиса, показывающие, как я тестирую, собираю и деплою.)

### Приложение Г: Глоссарий терминов

(Здесь будут определения всех умных слов, которые я использовал: Workflow, Job, Декаплинг, Идемпотентность и т.д.)

### Приложение Д: Руководство по развертыванию и эксплуатации

(Пошаговые инструкции, как развернуть всю платформу с нуля, а также как ее мониторить, делать бэкапы и обновлять.)

### Приложение F: Процедура тестирования

Для проверки работоспособности системы я использую `dummy-service` и `debug_producer.py`. Эти инструменты особенно эффективны в моей стандартизированной среде разработки `devcontainer`.

**1. `dummy-service`: Мой тестовый микросервис для симуляции**

Он может притворяться другими сервисами, проверять связь с Kafka и имитировать нагрузку.

*   **Запуск:** Запускаю его в Kubernetes как `Job` или `Pod`. Для локального тестирования в `devcontainer` использую:
    ```bash
    python3.11 -m app.main --debug --simulate-loading
    ```
*   **Подробнее:** См. `services/dummy-service/README.md`.

**2. `debug_producer.py`: Мой инструмент для отправки команд и проверки ответов**

Это CLI-инструмент для отправки тестовых команд (`ping`, `stop`) в Kafka и проверки ответов.

*   **Тестирование связности Kafka (ping/pong):**
    ```bash
    python3.11 services/dummy-service/debug_producer.py \
      --queue-id <your-queue-id> \
      --command ping \
      --expect-pong
    ```
*   **Тестирование команды остановки (stop):**
    ```bash
    python3.11 services/dummy-service/debug_producer.py \
      --queue-id <your-queue-id> \
      --command stop
    ```
*   **Тестирование имитации загрузки и отслеживания статуса:** Запускаю `dummy-service` с `--simulate-loading` и слежу за событиями в `queue-events`.
*   **Тестирование симуляции сбоя:** Запускаю `dummy-service` с `--fail-after N` и смотрю, как он отправляет `error` события.
*   **Тестирование Prometheus-метрик:** Проверяю метрики через `curl localhost:8000/metrics`.

**3. `devcontainer`: Моя стандартизированная среда разработки**

`devcontainer` — это Docker-контейнер, который дает мне полноценную среду разработки, интегрированную с VS Code. Это гарантирует, что у всех разработчиков одинаковое окружение.

**Ключевые особенности:**
*   **Базовый образ:** Ubuntu 22.04 LTS.
*   **Инструменты:** `kubectl`, Helm, `gitlab-runner`, `git`, `curl`, `ssh` и другие.
*   **Доступ к Kubernetes:** Автоматически настраивается.
*   **Пользователи и SSH:** Создается отдельный пользователь и настраивается SSH-доступ.
*   **Сертификаты:** Устанавливаются CA-сертификаты для доверия к внутренним сервисам.

**Как использовать:**
1.  Установить Docker Desktop и расширение "Dev Containers" для VS Code.
2.  Открыть проект StreamForge в VS Code и выбрать "Reopen in Container".
3.  VS Code сам соберет образ и запустит контейнер.

### Приложение G: Управление ресурсами Kafka

Мои манифесты Kubernetes в `cred-kafka-yaml/` позволяют декларативно управлять ресурсами Kafka через оператор Strimzi. Это включает создание топиков (`queue-control`, `queue-events`), пользователей Kafka (`user-streamforge`) и их прав доступа, а также хранение учетных данных.

### Приложение H: Среда отладки в Kubernetes

Для отладки и взаимодействия с кластером Kubernetes я использую:

*   **JupyterHub:** Позволяет запускать интерактивные сессии Jupyter Notebook прямо в кластере (Моя платформа для интерактивных ноутбуков). Мои образы ноутбуков уже содержат `kubectl`, `helm` и другие инструменты.

    **Ключевые особенности моей настройки JupyterHub:**
    *   **Управление неактивными серверами:** Автоматически завершает неактивные серверы Jupyter.
    *   **Аутентификация:** Используется простая "фиктивная" аутентификация для тестовой среды.
    *   **База данных Hub:** Используется `sqlite-memory`, но данные сохраняются на хосте.
    *   **Размещение подов:** Hub и пользовательские серверы запускаются на узле `k2w-8`.
    *   **Доступ:** Через Ingress по адресу `jupyterhub.dmz.home` с TLS.
    *   **Образы пользовательских серверов:** Используется кастомный образ `registry.dmz.home/streamforge/core-modules/jupyter-python311:v0.0.2` с нужными инструментами.
    *   **Ресурсы:** Гарантированный объем памяти для каждого сервера — `1G`.
    *   **Хранилище данных:** Используются персистентные тома, монтируемые с хоста, для `/home/`, `/data/project`, `/data/venv`.
    *   **Безопасность:** Поды запускаются с `UID: 1001` и `FSGID: 100`.
    *   **Docker Registry:** Используется секрет `regcred` для аутентификации.

*   **Dev Container (VS Code):** Подробно описан выше.

*   **Dev-контейнер (общий):** Это Docker-образ с широким набором инструментов (`kubectl`, `helm`, `kafkacat`, `python`), который можно использовать для запуска временных подов в Kubernetes для интерактивной отладки).