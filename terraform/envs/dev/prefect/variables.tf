variable "cluster_name" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "project_id" {
  type = string
}

variable "prefect_cloud_account_id" {
  type = string
}

variable "prefect_cloud_workspace_id" {
  type = string
}

variable "prefect_api_key" {
  type      = string
  sensitive = true
}
