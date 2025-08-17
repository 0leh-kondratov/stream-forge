# Project Setup

This directory contains Terraform configurations for the initial project setup, including:

- **`apis.tf`**: Enables necessary Google Cloud APIs.
- **`backend.tf`**: Configures the Terraform remote backend (e.g., Google Cloud Storage) for storing Terraform state.
- **`providers.tf`**: Defines the required Terraform providers (e.g., `google`).
- **`variables.tf`**: Defines input variables for the project configuration.
- **`versions.tf`**: Specifies the required Terraform and provider versions.

## Usage

To initialize and apply these configurations, run the following Terraform commands:

```bash
terraform init
terraform plan
terraform apply
```
