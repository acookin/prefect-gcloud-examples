variable "cluster_name" {
  type = string
}

variable "region" {
  type = string
}

variable "project_id" {
  type = string
}

variable "agent_namespace" {
  type    = string
  default = "prefect"
}

variable "helm_chart_version" {
  type    = string
  default = "2022.12.22"
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
  default   = ""
}

variable "create_namespace" {
  type    = bool
  default = true
}

variable "api_key_secret" {
  type = object({
    secret_name = string
    secret_key  = string
  })
  description = "name & key of k8s secret that contains the prefect cloud API key"
  default = {
    secret_name = "prefect-api-key"
    secret_key  = "key"
  }
}
