#!/bin/bash
set -e

echo "🚀 STARTUP — запуск окружения"

export DEBIAN_FRONTEND=noninteractive

# === 🔐 Параметры пользователя ===
USER_NAME=${USER_NAME:-kinga}
USER_ID=${USER_ID:-1001}
USER_PASSWORD=${USER_PASSWORD:-kinga123}

# === 🧑 Создание пользователя ===
if ! id "$USER_NAME" &>/dev/null; then
    echo "🧑 Создаю пользователя $USER_NAME (UID=$USER_ID)"
    groupadd -g "$USER_ID" "$USER_NAME"
    useradd -m -s /bin/bash -u "$USER_ID" -g "$USER_ID" "$USER_NAME"
    echo "$USER_NAME:$USER_PASSWORD" | chpasswd

    # 🔁 Гарантируем загрузку .bashrc из .profile
    echo 'if [ -f ~/.bashrc ]; then . ~/.bashrc; fi' >> /home/$USER_NAME/.profile
    chown $USER_NAME:$USER_NAME /home/$USER_NAME/.profile
fi

# === 🗝️ Настройка SSH-ключей ===
if [[ -n "$SSH_AUTHORIZED_KEYS" ]]; then
    echo "🔐 Настраиваю authorized_keys"
    mkdir -p /home/$USER_NAME/.ssh
    echo "$SSH_AUTHORIZED_KEYS" > /home/$USER_NAME/.ssh/authorized_keys
    chown -R "$USER_NAME:$USER_NAME" "/home/$USER_NAME/.ssh"
    chmod 700 "/home/$USER_NAME/.ssh"
    chmod 600 "/home/$USER_NAME/.ssh/authorized_keys"
fi

# === 📌 Kubernetes ENV vars ===
KUBE_API_IP=$(getent hosts kubernetes.default.svc | awk '{ print $1 }')
if [[ -n "$KUBE_API_IP" ]]; then
    echo "🌐 Настраиваю Kubernetes переменные окружения..."
    cat <<EOF > /etc/profile.d/k8s_env.sh
    export KUBERNETES_SERVICE_HOST=${KUBE_API_IP}
    export KUBERNETES_SERVICE_PORT=443
EOF
    chmod +x /etc/profile.d/k8s_env.sh
fi

# === 🔁 Настройка SSH ===
echo "🛠 Настраиваю sshd_config..."
cat <<EOF > /etc/ssh/sshd_config
Port 22
PermitRootLogin no
PasswordAuthentication yes
PermitEmptyPasswords no
PermitUserEnvironment yes
AllowTcpForwarding yes
PermitTunnel yes
PermitOpen any
GatewayPorts yes
X11Forwarding no
ClientAliveInterval 60
ClientAliveCountMax 3
LoginGraceTime 30
UseDNS no
EOF

mkdir -p /run/sshd

# === ⚙️ Установка GitLab Runner (если есть) ===
if [ -f /usr/local/bin/gitlab-runner ]; then
    echo "⚙️ Установка GitLab Runner сервисно"
    gitlab-runner install --user=${USER_NAME} --working-directory=/home/${USER_NAME}
    gitlab-runner start
else
    echo "⚠️ GitLab Runner не найден"
fi

# === 📜 Добавление CA сертификата ===
if [[ -f /usr/local/share/ca-certificates/dev-ca.crt ]]; then
    echo "📜 Устанавливаю CA сертификат..."
    update-ca-certificates
else
    echo "⚠️ CA сертификат не найден!"
fi

# === 🚪 Запуск SSH ===
echo "🔑 Запуск SSHD (foreground)"
exec /usr/sbin/sshd -D
