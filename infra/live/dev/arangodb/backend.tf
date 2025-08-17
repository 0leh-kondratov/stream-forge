terraform {
  backend "http" {
    address        = "https://gitlab.dmz.home/api/v4/projects/136/terraform/state/${var.tf_state_name}"
    lock_address   = "https://gitlab.dmz.home/api/v4/projects/136/terraform/state/${var.tf_state_name}/lock"
    unlock_address = "https://gitlab.dmz.home/api/v4/projects/136/terraform/state/${var.tf_state_name}/lock"
    username       = "kinga"
    password       = "$GITLAB_ACCESS_TOKEN"
    lock_method    = "POST"
    unlock_method  = "DELETE"
    retry_wait_min = 5
  }
}

variable "tf_state_name" {
  description = "The name of the Terraform state file in GitLab."
  type        = string
}
