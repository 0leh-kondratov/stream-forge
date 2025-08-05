FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV KUBE_VERSION="v1.28.15"
ENV HELM_VERSION="3.16.3"
ENV GITLAB_RUNNER_VERSION="latest"

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo openssh-server openssh-sftp-server ca-certificates \
    net-tools curl iputils-ping bash curl git \
    dnsutils mc nano traceroute xz-utils tar glusterfs-client \
    whois nmap tcpdump mtr-tiny iproute2 libnss3\
  && apt-get clean && rm -rf /var/lib/apt/lists/* \
  \
  # 🔹 Установка kubectl
  && curl -LO "https://dl.k8s.io/release/${KUBE_VERSION}/bin/linux/amd64/kubectl" \
  && chmod +x kubectl \
  && mv kubectl /usr/local/bin/kubectl \
  \
  # 🔹 Установка helm (последняя версия)
  && curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 \
  && chmod 700 get_helm.sh \
  && ./get_helm.sh \
  && rm get_helm.sh

# Установка GitLab Runner
RUN curl -L https://gitlab-runner-downloads.s3.amazonaws.com/${GITLAB_RUNNER_VERSION}/binaries/gitlab-runner-linux-amd64 -o /usr/local/bin/gitlab-runner && \
    chmod +x /usr/local/bin/gitlab-runner  

# 🔹 Добавляем скрипт запуска (например, для sshd)
COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh \
    && mkdir -p /var/run/sshd

EXPOSE 22

ENTRYPOINT ["/usr/local/bin/startup.sh"]
