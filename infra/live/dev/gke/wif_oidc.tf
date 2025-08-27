# Пул федерации
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
}

# Провайдер OIDC для GitHub
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub OIDC Provider"

  oidc { issuer_uri = "https://token.actions.githubusercontent.com" }

  # Рекомендуемый mapping атрибутов для GitHub OIDC
  attribute_mapping = {
    "google.subject"        = "assertion.sub"
    "attribute.actor"       = "assertion.actor"
    "attribute.repository"  = "assertion.repository"
    "attribute.ref"         = "assertion.ref"
    "attribute.workflow"    = "assertion.workflow"
    "attribute.sha"         = "assertion.sha"
  }

  # Жестко ограничиваемся вашим репозиторием и веткой
  attribute_condition = "assertion.repository == '${var.github_repo}' && assertion.ref == '${var.github_ref}'"
}

# Сервисный аккаунт, под который будет логиниться GitHub Actions
resource "google_service_account" "github_cicd" {
  account_id   = "github-cicd"
  display_name = "GitHub CI/CD SA"
}

# Разрешаем субъектам из пула (с атрибутом repository) импользовать (impersonate) этот SA
resource "google_service_account_iam_member" "allow_wif_impersonate" {
  service_account_id = google_service_account.github_cicd.name
  role               = "roles/iam.workloadIdentityUser"
  # principalSet c фильтром по репозиторию — безопасный паттерн
  member = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

# Проектные роли для сборки/пуша/деплоя (сузьте при необходимости)
resource "google_project_iam_member" "gsa_cloudbuild" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.github_cicd.email}"
}

resource "google_project_iam_member" "gsa_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_cicd.email}"
}

resource "google_project_iam_member" "gsa_container_admin" {
  project = var.project_id
  role    = "roles/container.admin"
  member  = "serviceAccount:${google_service_account.github_cicd.email}"
}