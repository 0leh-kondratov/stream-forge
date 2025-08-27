resource "kubernetes_cluster_role_binding" "github_cicd_admin" {
  metadata { name = "github-cicd-admin" }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = "cluster-admin"
  }

  subject {
    kind      = "User"
    name      = google_service_account.github_cicd.email  # user:<GSA_EMAIL>
    api_group = "rbac.authorization.k8s.io"
  }
}