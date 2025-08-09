# Этот Dockerfile создает кастомный образ для CI/CD, содержащий Kaniko, Git и Curl.

# Используем Alpine в качестве базового образа, т.к. он легкий.
FROM alpine:3.18 as final

# Копируем ваш кастомный CA сертификат в образ
COPY ca.crt /usr/local/share/ca-certificates/ca.crt

# Устанавливаем git, curl и ca-certificates (для работы с HTTPS)
RUN apk add --no-cache \
    git \
    curl \
    ca-certificates && \
    # Обновляем хранилище сертификатов, чтобы система доверяла вашему CA
    update-ca-certificates

# Копируем исполняемый файл Kaniko и его конфигурацию из официального образа Kaniko.
# Мы используем конкретную версию, чтобы сборка была воспроизводимой.
COPY --from=gcr.io/kaniko-project/executor:v1.22.0-debug /kaniko/ /kaniko/

# Точка входа по умолчанию - сам Kaniko, чтобы образ можно было использовать так же,
# как и официальный.
ENTRYPOINT ["/kaniko/executor"]

