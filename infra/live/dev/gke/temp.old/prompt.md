Сгенерируй ПОЛНЫЙ Terraform-набор для развёртывания GKE Autopilot кластера (dev) в GCP. Хочу получить готовые .tf файлы, чтобы положить их в репозиторий и применить одной командой.

Требования:
- Структура каталога: infra/live/dev/gke/
- Файлы: 
  1) versions.tf
  2) variables.tf
  3) providers.tf
  4) apis.tf
  5) network.tf
  6) cluster.tf
  7) outputs.tf
  8) terraform.tfvars (пример с моими значениями)

Версии/инструменты:
- Terraform >= 1.6
- Провайдер google ~> 6.0
- Никаких внешних модулей — только нативные ресурсы провайдера.

Переменные и значения по умолчанию:
- project_id (string, без default)
- region (string, default = "us-central1")
- cluster_name (string, default = "gke-free-autopilot")
- vpc_cidr (string, default = "10.0.0.0/16")
- pods_cidr (string, default = "10.1.0.0/16")
- services_cidr (string, default = "10.2.0.0/20")

Что должно делать решение:

1) providers.tf
   - provider "google" с использованием var.project_id и var.region.

2) apis.tf
   - Включи API: 
     serviceusage.googleapis.com,
     cloudresourcemanager.googleapis.com,
     compute.googleapis.com,
     iam.googleapis.com,
     container.googleapis.com  (Kubernetes Engine API)
   - Для включения используй ресурсы google_project_service.
   - Сделай так, чтобы кластер зависел от включения container.googleapis.com.

3) network.tf
   - Создай кастомную VPC (google_compute_network) с auto_create_subnetworks = false.
   - Создай сабнет (google_compute_subnetwork) в var.region с primary CIDR = var.vpc_cidr.
   - Добавь два secondary диапазона: 
     range_name "pods" = var.pods_cidr,
     range_name "services" = var.services_cidr.
   - Зависимости: сеть создаётся только после включения Compute API (или всего набора common APIs).

4) cluster.tf
   - Региональный кластер Autopilot:
     resource "google_container_cluster" с полями:
       name              = var.cluster_name
       location          = var.region
       enable_autopilot  = true
       network           = google_compute_network.vpc.id
       subnetwork        = google_compute_subnetwork.subnet.id
       networking_mode   = "VPC_NATIVE"
       ip_allocation_policy { cluster_secondary_range_name = "pods", services_secondary_range_name = "services" }
       deletion_protection = false
       logging_config { enable_components = ["SYSTEM_COMPONENTS"] }  # чтобы не собирать логи workload'ов
     - depends_on = [ресурс включения container.googleapis.com]
   - НИКАКИХ node_pool — в Autopilot они не задаются вручную.

5) outputs.tf
   - Выведи:
     output "cluster_name" (raw имя кластера),
     output "cluster_region" (var.region),
     output "get_credentials_hint" — строка с готовой командой:
       gcloud container clusters get-credentials ${cluster_name} --region ${cluster_region} --project ${var.project_id}

6) terraform.tfvars (пример)
   - Приведи пример со значениями:
     project_id  = "stream-forge-4"
     region      = "us-central1"
     cluster_name = "gke-free-autopilot"
     # при необходимости можно переопределить CIDR'ы

Ограничения/правила:
- Никаких ресурсов в kube-system — это управляемое пространство GKE Autopilot (упомяни в комментариях).
- Код должен быть минималистичным и «дешёвым по умолчанию».
- Все depends_on должны быть статическими (без for-each comprehension внутри depends_on).
- Не используй внешние LoadBalancer'ы в примерах/подсказках вывода.
- Добавь короткий README-комментарий в outputs или в конце ответа: как применить и как подключиться kubectl.

Выход:
- Дай полный код КАЖДОГО файла из списка (1–8), без многоточий, чтобы я мог сразу запустить:
  terraform -chdir=infra/live/dev/gke init
  terraform -chdir=infra/live/dev/gke plan
  terraform -chdir=infra/live/dev/gke apply -auto-approve
- В конце добавь блок «Smoke test» в комментарии (yaml-манифест Deployment+Service c ClusterIP и маленькими requests, и команду port-forward), но не добавляй его в Terraform — просто как инструкцию к проверке.
