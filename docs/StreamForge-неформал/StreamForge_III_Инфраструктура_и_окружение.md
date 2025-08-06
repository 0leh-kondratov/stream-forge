## Часть III: Инфраструктура и окружение

StreamForge развернут на базе Kubernetes-платформы в локальной лаборатории.

### Глава 5: Основы платформы: Kubernetes и виртуализация

(Базовые конфиги для Kubernetes).

#### 5.1. Фундамент: Proxmox VE

Используется `Proxmox VE` для виртуализации. Это позволяет эффективно управлять физическими ресурсами, создавать виртуальные машины для узлов Kubernetes и изолировать окружение.

#### 5.2. Развертывание кластера: Kubespray

Кластер Kubernetes развернут с помощью `Kubespray`. Этот инструмент позволяет автоматизировать и стандартизировать процесс создания production-ready кластера.

#### 5.3. Сетевая инфраструктура

*   **`kube-vip` для высокой доступности:** Для обеспечения высокой доступности Kubernetes API используется `kube-vip`. Он предоставляет виртуальный IP-адрес, который обеспечивает бесперебойную работу в случае отказа одного из управляющих узлов.
*   **`MetalLB` для внешнего доступа:** В лабораторных условиях, где отсутствуют аппаратные балансировщики нагрузки, `MetalLB` (версия `0.14.9`) (Балансировщик нагрузки для моей bare-metal лаборатории) позволяет использовать стандартные Kubernetes-сервисы типа `LoadBalancer` и предоставлять внешние IP-адреса для доступа к приложениям.

#### 5.4. Ingress и Gateway API: Управление трафиком

Для управления внешним трафиком используются два Ingress-контроллера: `Traefik` и `ingress-nginx`. `Traefik` является предпочтительным решением благодаря поддержке нового **Gateway API**, который предоставляет расширенные возможности для маршрутизации трафика. `ingress-nginx` (версия `4.12.1`) установлен в качестве резервного варианта.

**Конфигурация Traefik (версия `36.1.0`):**
*   **Точки входа:**
    *   `web`: HTTP (порт 80), с перенаправлением на HTTPS.
    *   `websecure`: HTTPS (порт 443) с TLS.
    *   `ssh`: TCP (порт 2222).
    *   `kafka`: TCP (порт 9094).
*   **Панель мониторинга:** Доступна по адресу `traefik.dmz.home/dashboard`.
*   **Сертификаты:** Автоматически выпускаются `cert-manager` с помощью `homelab-ca-issuer`.
*   **Хранение:** Используется `1Gi` персистентного хранилища на `nfs-client` для данных ACME.
*   **Внешний IP:** `192.168.1.153`.

#### 5.5. DNS и TLS

*   **`Technitium DNS Server`:** Локальный DNS-сервер, который позволяет обращаться к сервисам по доменным именам (например, `jupyterhub.dmz.home`).
*   **`cert-manager`:** Автоматизирует управление TLS-сертификатами для всех сервисов, обеспечивая безопасность соединений.

##### Скрипт `script.sh` для создания TLS-сертификатов

Скрипт `/platform/base/cert/script.sh` автоматизирует процесс создания и получения TLS-сертификатов с использованием `openssl` и `cert-manager` в среде Kubernetes.

Основные шаги скрипта:
1.  **Настройка переменных**: Определяются параметры, такие как пространство имен Kubernetes, имя сертификата, домен, IP-адрес, срок действия сертификата и директория для сохранения файлов.
2.  **Генерация ключа и CSR**: Используется `openssl` для создания приватного ключа и запроса на подпись сертификата (CSR) с альтернативными именами субъекта (SAN) для доменного имени и IP-адреса.
3.  **Создание CertificateRequest**: CSR кодируется в Base64, и на его основе динамически формируется YAML-манифест для объекта `CertificateRequest` `cert-manager`, который затем применяется к кластеру Kubernetes.
4.  **Ожидание и получение сертификата**: Скрипт ожидает выполнения `CertificateRequest` `cert-manager`'ом. После успешного выполнения извлекает сгенерированный сертификат, декодирует его и сохраняет в файл.
5.  **Проверка**: Выполняются команды `openssl` для проверки соответствия приватного ключа и сертификата, а также для вывода подробной информации о сертификате.

## Глава 6: Где я храню все эти данные?

Надежное хранилище — это очень важно. Я использую несколько решений для разных типов данных:

#### 6.1. Обзор Storage-решений

*   **`Linstor Piraeus` (RWO):** Для баз данных (ArangoDB, PostgreSQL) я использую `Linstor Piraeus`. Это высокопроизводительное блочное хранилище с низкой задержкой.
*   **`GlusterFS` и `NFS Subdir External Provisioner` (RWX):** (Распределенная файловая система для общих томов). Для общих файлов (например, домашние директории JupyterHub) я использую `GlusterFS` и `NFS Subdir External Provisioner` (версия `4.0.18`). Это позволяет нескольким подам одновременно читать и писать в одно и то же хранилище. Мой NFS-сервер находится по адресу `192.168.1.6` и использует путь `/data0/k2`.

#### 6.2. Объектное хранилище Minio

`Minio` — это мой личный S3-совместимый "облачный" склад внутри кластера. Я использую его для:
1.  **Моделей машинного обучения:** `gnn-trainer` сохраняет сюда обученные модели, их веса и метрики.
2.  **Бэкапов:** Здесь хранятся резервные копии всех важных данных.

## Глава 7: Моя платформа данных: Как я управляю информацией

Платформа данных — это сердце StreamForge.

#### 7.1. `Strimzi Kafka Operator`: Мой личный Kafka-менеджер

`Strimzi` (Развертывание Apache Kafka с помощью оператора Strimzi) позволяет мне легко управлять Apache Kafka в Kubernetes. Он автоматизирует все сложные задачи: развертывание, настройку, управление топиками и пользователями, а также обеспечивает высокую доступность.

#### 7.2. Мультимодельная база данных `ArangoDB`

Я выбрал `ArangoDB` из-за ее гибкости. Она может хранить данные как документы (JSON) и как графы, что идеально подходит для моего проекта:
*   **Документы:** Для исторических свечей, сделок и статусов задач.
*   **Графы:** Для анализа связей между активами и обучения GNN-моделей.

#### 7.3. Реляционная база данных `PostgreSQL` (Zalando Operator)

Для более структурированных данных (например, пользовательские настройки) я использую `PostgreSQL`. Оператор от Zalando (Управляет PostgreSQL кластерами) делает управление им очень простым.

#### 7.4. Автомасштабирование с `KEDA`: Экономия ресурсов

`KEDA` позволяет мне автоматически масштабировать количество "рабочих лошадок" в зависимости от нагрузки. Если в Kafka накопилось много сообщений, KEDA запустит больше консьюмеров, а когда нагрузка спадет — уменьшит их количество. Это очень удобно для оптимизации ресурсов!

#### 7.5. kafka-ui: Веб-интерфейс для Kafka

`kafka-ui` — это веб-интерфейс для управления Kafka.

*   **Версия:** `v0.7.2` (образ `provectuslabs/kafka-ui:v0.7.2`)
*   **Доступ:** Доступен через Ingress по адресу `kafka-ui.dmz.home` с использованием `nginx` Ingress-контроллера и TLS-сертификата (`kafka-ui-tls`).
*   **Размещение подов:** Настроен на запуск на узле `k2w-7` с помощью `nodeSelector`.
*   **Реплики:** Развернут в одном экземпляре (`replicaCount: 1`).
*   **Подключение к Kafka:** Подключается к Kafka кластеру `k3` по адресу `k3-kafka-bootstrap.kafka:9093` с использованием `SASL_SSL` и механизма аутентификации `SCRAM-SHA-512` с пользователем `user-streamforge`.

## Глава 8: Все под контролем: Как я слежу за системой

Понимать, что происходит в моей распределенной системе, очень важно.

#### 8.1. Метрики: `Prometheus`, `cAdvisor`, `NodeExporter`

Я использую `Prometheus` для сбора и хранения всех метрик. `NodeExporter` собирает данные с моих серверов, `cAdvisor` — с контейнеров, а каждый мой микросервис отправляет свои собственные метрики.

**Ключевые особенности:**
*   **Версия:** `kube-prometheus-stack-71.1.0`.
*   **Prometheus:** Хранит данные на `20Gi` NFS-хранилище. Доступен через Ingress по адресу `prometheus.dmz.home`.
*   **Alertmanager:** Хранит данные на `500Mi` NFS-хранилище.
*   **Grafana:** Использует `1Gi` NFS-хранилище для персистентности. Доступна через Ingress по адресу `grafana.dmz.home`.
*   Все Ingress-ресурсы защищены TLS-сертификатами, выданными `cert-manager`.

#### 8.2. Логи: `Fluent-bit`, `Elasticsearch`, `Kibana`

(Мой стек для сбора и анализа логов (Elasticsearch, Logstash, Kibana)).
Моя система логирования очень продвинутая. Я собираю как структурированные логи из приложений, так и системные логи с узлов.

**Как это работает:**
1.  **Логи приложений:** Мои приложения отправляют логи напрямую в `Fluent-bit` по сети. `Fluent-bit` использует специальный Lua-скрипт, чтобы динамически создавать индексы в Elasticsearch на основе тегов и даты (например, `internal-my-app-2025.08.06`). Это очень удобно для поиска и управления старыми логами.
2.  **Системные логи:** `Fluent-bit` также собирает логи из `/var/log/syslog`, `/var/log/nginx/access.log` и `/var/log/auth.log`.
3.  **Elasticsearch и Kibana:** `Elasticsearch` хранит и индексирует все логи, а `Kibana` предоставляет удобный веб-интерфейс для их просмотра и анализа. Доступ к Kibana защищен TLS.

**Примеры (для разработчиков):**
*   **Отправка логов из Python:**
    ```python
    from fluent import sender
    import time
    import random
    import json

    APP_NAME = "my-pod-app"

    logger = sender.FluentSender(
        tag='internal.' + APP_NAME, # Важно: тег определяет будущий индекс!
        host='fluent-bit-service.logging.svc.cluster.local',
        port=24224
    )

    log_record = {
        'message': 'User logged in successfully',
        'level': 'INFO',
        'user_id': 12345
    }
    logger.emit('log', log_record)
    ```
*   **Lua-скрипт для Fluent-bit (создание индекса):**
    ```lua
    function cb_set_index(tag, timestamp, record)
        local t = os.time()
        if timestamp and type(timestamp) == "table" and timestamp[1] > 0 then
            t = timestamp[1]
        end

        local prefix = "unknown"
        local app = "unknown"

        local parts = {}
        for part in string.gmatch(tag, "([^"."]+)") do
            table.insert(parts, part)
        end
        if #parts >= 2 then
            prefix = parts[1]
            app = parts[2]
        end

        local date = os.date("%Y.%m.%d", t)
        record["log_index"] = prefix .. "-" .. app .. "-" .. date
        return 1, timestamp, record
    end
    ```

**Инструменты для отладки:**
*   **`test-logger-script`:** Простой Python-скрипт для генерации тестовых логов.
*   **`fluentbit-tailon`:** Специальный инструмент для просмотра "сырых" логов в реальном времени.

#### 8.3. Визуализация и алертинг: `Grafana`, `Alertmanager`

`Grafana` — моя любимая панель для визуализации метрик из Prometheus и логов из Elasticsearch. `Alertmanager` интегрирован с Prometheus и отправляет мне уведомления в Telegram, если что-то идет не так.

## Глава 9: Автоматизация и GitOps: Мой путь к ленивому деплою

Автоматизация сборки, тестирования и развертывания — это основа моей работы.

#### 9.1. `GitLab Runner`: Мой личный CI/CD-помощник

`GitLab Runner` (Запускает мои CI/CD пайплайны в Kubernetes) выполняет все задачи, описанные в `.gitlab-ci.yml`. Я использую `kubernetes` executor, что означает, что для каждой задачи Runner создает отдельный Pod в моем кластере. Для сборки Docker-образов я использую `Kaniko` (без Docker-in-Docker!).

##### 9.1.1. Конфигурация и особенности исполнителя (Runner)

**Общие настройки Runner:**
*   **Исполнитель:** `kubernetes`. Каждый CI/CD job запускается в отдельном Pod'е в неймспейсе `gitlab`.
*   **Привязка к узлу:** Runner запускает поды только на узле `k2w-9`.
*   **Права доступа:** Использует `ServiceAccount` `full-access-sa` и работает в привилегированном режиме.
*   **Образ по умолчанию:** `ubuntu:22.04`.
*   **Ресурсы:** Запрос: 100m CPU, 128Mi RAM. Лимит: 500m CPU, 512Mi RAM.
*   **Кэширование:** Использует распределенное кэширование на базе S3 (мой внутренний Minio на `minio.dmz.home`, бакет `runner-cache`).
*   **Docker Registry:** Секрет `regcred` монтируется для аутентификации с приватными репозиториями.
*   **TLS:** Секрет `home-certificates` монтируется для доверия к внутренним TLS-сертификатам.

**Специфическая конфигурация `stf-runner` (k2m-runner):**
*   **Имя:** `k2m-runner` (в `helm list` он отображается как `stf-runner`).
*   **Версия:** `0.79.0` (приложение `18.2.0`).
*   **URL GitLab:** `https://gitlab.dmz.home/`
*   **Пространство имен Kubernetes:** `gitlab`
*   **Таймаут опроса:** 300 секунд.
*   **Монтирование томов:** `docker-config`, `home-certificates`, `runner-home` (PVC `gitlab-runner-home`).

##### 9.1.2. Структура CI/CD пайплайна

Мой CI/CD пайплайн состоит из нескольких стадий:
*   **`setup`**: Подготовка (например, настройка Kubernetes RBAC).
*   **`build`**: Сборка Docker-образов (использую `Kaniko`).
*   **`test`**: Запуск автоматических тестов.
*   **`deploy`**: Развертывание в Kubernetes.

Задачи запускаются автоматически при изменениях в файлах или вручную.

##### 9.1.3. Детализация конфигурации пайплайнов

Я использую модульный подход с `include` и `extends` в GitLab CI, чтобы не дублировать код.

**Основной файл `.gitlab-ci.yml`:**
Он включает конфигурации для отдельных сервисов и платформы.
```yaml
stages:
  - setup
  - build
  - test
  - deploy

include:
  - '/services/queue-manager/.gitlab-ci.yml'
  - '/services/loader-api-trades/.gitlab-ci.yml'
  - '/services/loader-api-candles/.gitlab-ci.yml'
  - '/services/arango-connector/.gitlab-ci.yml'
  - '/services/dummy-service/.gitlab-ci.yml'
  - 'platform/.gitlab-ci.yml' # Включаем конфигурацию для платформы (базовый образ, RBAC)
```

**Шаблоны CI/CD (`.gitlab/ci-templates/`):**
Общие шаблоны для Python-сервисов.
```yaml
.build_python_service:
  stage: build
  image: gcr.io/kaniko-project/executor:debug
  script:
    - SERVICE_VERSION=$(cat $CI_PROJECT_DIR/$SERVICE_PATH/VERSION)
    - /kaniko/executor
      --context $CI_PROJECT_DIR/$SERVICE_PATH
      --dockerfile Dockerfile
      --destination $CI_REGISTRY_IMAGE/$SERVICE_NAME:$SERVICE_VERSION
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      changes:
        - $SERVICE_PATH/**/*
        - libs/**/*
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - $SERVICE_PATH/**/*
        - libs/**/*
    - when: manual
      allow_failure: false
```

**Конфигурация для отдельных сервисов:**
Каждый сервис расширяет общий шаблон.
```yaml
include:
  - project: 'kinga/stream-forge'
    ref: main
    file: '/.gitlab/ci-templates/Python-Service.gitlab-ci.yml'

build-dummy-service:
  extends: .build_python_service
  variables:
    SERVICE_NAME: dummy-service
    SERVICE_PATH: services/dummy-service

deploy-dummy-service:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl apply -f $CI_PROJECT_DIR/services/dummy-service/k8s/dummy-service-deployment.yaml
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: on_success
```

**Конфигурация для компонентов платформы:**
Аналогично сервисам.
```yaml
include:
  - project: 'kinga/stream-forge'
    ref: main
    file: '/.gitlab/ci-templates/Python-Service.gitlab-ci.yml' # Используем тот же шаблон для сборки базового образа

build-base-image:
  extends: .build_python_service
  variables:
    SERVICE_NAME: base
    SERVICE_PATH: platform # Указываем путь к Dockerfile и VERSION для базового образа

apply-rbac:
  stage: setup
  image: bitnami/kubectl:latest
  script:
    - kubectl apply -f $CI_PROJECT_DIR/input/cred-kafka-yaml/full-access-sa.yaml
    - kubectl apply -f $CI_PROJECT_DIR/input/cred-kafka-yaml/full-access-sa-binding.yaml
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - input/cred-kafka-yaml/full-access-sa.yaml
        - input/cred-kafka-yaml/full-access-sa-binding.yaml
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      changes:
        - input/cred-kafka-yaml/full-access-sa.yaml
        - input/cred-kafka-yaml/full-access-sa-binding.yaml
    - when: manual
      allow_failure: false
```
Такая структура обеспечивает гибкость, переиспользование и легкую масштабируемость CI/CD пайплайнов в проекте StreamForge.

#### 9.2. `ArgoCD`: Мой GitOps-волшебник

`ArgoCD` (Мой GitOps-инструмент для деплоя в Kubernetes) — это то, что позволяет мне реализовать GitOps. Он постоянно следит за моим Git-репозиторием и синхронизирует состояние кластера с тем, что там описано. Это гарантирует, что мой кластер всегда выглядит так, как я хочу, и позволяет легко откатываться к предыдущим версиям.

**Ключевые особенности моей настройки:**
*   **GitOps-репозиторий:** `iac_kubeadm` (`https://gitlab.dmz.home/infra-a-cod/iac_kubeadm.git`) — это мой "источник правды" для кластера.
*   **Доступ к серверу:** Пока что ArgoCD API-сервер доступен без TLS (для удобства в домашней лабе), но доступ к веб-интерфейсу (`argocd.dmz.home`) защищен.
*   **Отказоустойчивость:** Сейчас все ключевые компоненты ArgoCD работают в одном экземпляре, так что это не высокодоступная конфигурация (но для pet-проекта сойдет!).
*   **CRD:** При удалении чарта ArgoCD, все его Custom Resource Definitions тоже удаляются.
*   **Интеграция с GitLab:** Есть TLS-сертификат для `gitlab.dmz.home`, чтобы ArgoCD мог безопасно подключаться к моим репозиториям.

#### 9.3. `Reloader`: Автоматические перезагрузки

`Reloader` — это маленький, но очень полезный инструмент. Он следит за изменениями в `ConfigMap` и `Secret`. Если я обновляю какой-то конфиг или секрет, `Reloader` автоматически перезапускает связанные с ним приложения, чтобы они подхватили новые настройки. Очень удобно!

## Глава 10: Безопасность и другие фишки

### 10.1. Секреты: `HashiCorp Vault` и `Vault CSI Driver`

Для безопасного хранения паролей, API-ключей и других секретов я использую `HashiCorp Vault`. `Vault CSI Driver` позволяет моим подам получать секреты, монтируя их как временные тома. Это намного безопаснее, чем хранить их в Kubernetes `Secret` объектах.

### 10.2. Аутентификация: `Keycloak`

`Keycloak` (Сервер для управления идентификацией и доступом) — мой центральный сервер для управления пользователями и доступом. Он обеспечивает единый вход (SSO) для всех моих веб-интерфейсов: Grafana, Kibana, ArgoCD и, конечно, будущего UI StreamForge.

### 10.3. Ускорение вычислений: `NVIDIA GPU Operator`

(Поддержка GPU в Kubernetes).
Для задач машинного обучения, которые требуют много вычислительной мощности, я использую `NVIDIA GPU Operator`. Он автоматизирует установку драйверов и других компонентов NVIDIA, делая мои GPU доступными для контейнеров. Это очень важно для эффективного обучения GNN-моделей!

**Ключевые особенности:**
*   **Версия:** `v24.9.2`.
*   **Конфигурация:** Используются стандартные настройки Helm-чарта. Никаких кастомных параметров, что упрощает обновления.
*   **Функциональность:** Оператор сам находит GPU на узлах и делает их доступными для подов.

### 10.4. Прочие утилиты

*   **`kubed`:** Помогает синхронизировать `ConfigMap` и `Secret` между разными неймспейсами.
*   **`Mailrelay`:** Мой центральный SMTP-шлюз для отправки уведомлений (например, от `Alertmanager`).