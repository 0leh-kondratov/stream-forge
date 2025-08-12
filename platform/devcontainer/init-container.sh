#!/bin/bash
set -e

: "${USER_NAME:=devuser}"
: "${USER_ID:=1000}"
: "${USER_PASSWORD:=changeme}"

echo "🔧 Creating user '$USER_NAME' (UID: $USER_ID)"
if ! id "$USER_NAME" > /dev/null 2>&1; then
    groupadd -g "$USER_ID" "$USER_NAME"
    useradd -m -s /bin/bash -u "$USER_ID" -g "$USER_ID" "$USER_NAME"
    echo "$USER_NAME:$USER_PASSWORD" | chpasswd
    usermod -aG sudo "$USER_NAME"
fi

HOME_DIR="/home/$USER_NAME"
mkdir -p "$HOME_DIR/.ssh"
chmod 700 "$HOME_DIR/.ssh"

# 🔐 Installing SSH keys and configuration (from Secret)
if [ -f "/run/secrets/ssh_authorized_keys" ]; then
    echo "📥 Installing SSH public key..."
    cp /run/secrets/ssh_authorized_keys "$HOME_DIR/.ssh/authorized_keys"
    chmod 600 "$HOME_DIR/.ssh/authorized_keys"
    chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.ssh/authorized_keys"
fi

if [ -f "/run/secrets/ssh_config" ]; then
    cp /run/secrets/ssh_config "$HOME_DIR/.ssh/config"
    chmod 600 "$HOME_DIR/.ssh/config"
    chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.ssh/config"
fi

if [ -f "/run/secrets/ssh_private_key" ]; then
    cp /run/secrets/ssh_private_key "$HOME_DIR/.ssh/id_rsa"
    chmod 600 "$HOME_DIR/.ssh/id_rsa"
    chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.ssh/id_rsa"
fi

# 🔧 XRDP: creating Openbox session
echo "exec openbox-session" > "$HOME_DIR/.xsession"
chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.xsession"

# 🛡️ Custom CA (optional)
if [ -f /usr/local/share/dev-ca.crt ]; then
    echo "🔐 Installing custom CA certificate..."
    mkdir -p /usr/local/share/ca-certificates/extra
    cp /usr/local/share/dev-ca.crt /usr/local/share/ca-certificates/extra/dev-ca.crt
    update-ca-certificates
fi

# 🛠️ Update SSH settings
function set_sshd_option {
    local key="$1"
    local value="$2"
    grep -q "^${key}" /etc/ssh/sshd_config && \
        sed -i "s|^${key}.*|${key} ${value}|" /etc/ssh/sshd_config || \
        echo "${key} ${value}" >> /etc/ssh/sshd_config
}

set_sshd_option PermitRootLogin yes
set_sshd_option X11Forwarding yes
set_sshd_option PermitTunnel yes
set_sshd_option AllowTcpForwarding yes
set_sshd_option ClientAliveInterval 0
set_sshd_option ServerAliveInterval 0

# ✅ Starting services
echo "🚀 Starting sshd and xrdp..."
/etc/init.d/xrdp start
exec /usr/sbin/sshd -D

