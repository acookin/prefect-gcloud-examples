terraform {
  required_providers {
    # helm = {
    #   source = "hashicorp/helm"
    # }
    google = {
      source = "hashicorp/google"
    }
    kubernetes = {
      source = "hashicorp/kubernetes"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}


data "google_client_config" "provider" {}

data "google_container_cluster" "cluster" {
  name     = var.cluster_name
  location = var.region
}

# provider "helm" {
#   kubernetes {
#     host  = "https://${data.google_container_cluster.cluster.endpoint}"
#     token = data.google_client_config.provider.access_token
#     cluster_ca_certificate = base64decode(
#       data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate
#     )
#   }
# }


provider "kubernetes" {
  host  = "https://${data.google_container_cluster.cluster.endpoint}"
  token = data.google_client_config.provider.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.cluster.master_auth[0].cluster_ca_certificate,
  )
}

resource "kubernetes_namespace" "prefect" {
  count = var.create_namespace ? 1 : 0
  metadata {
    name = var.agent_namespace
  }
}

resource "kubernetes_secret" "prefect_api_key" {
  count = var.prefect_api_key == "" ? 0 : 1
  metadata {
    name      = var.api_key_secret.secret_name
    namespace = var.agent_namespace
  }

  data = {
    key = var.prefect_api_key
  }
}

# resource "helm_release" "agent" {
#   name       = "prefect-agent"
#   namespace  = var.agent_namespace
#   repository = "https://prefecthq.github.io/prefect-helm/"
#   chart      = "prefect-agent"
#   version    = var.helm_chart_version

#   # uncomment if you want to supply your own values file, otherwise - use the set blocks below
#   # https://github.com/PrefectHQ/prefect-helm/blob/main/charts/prefect-agent/values.yaml
#   # values = [
#   #   "${file("values.yaml")}"
#   # ]

#   set {
#     name  = "agent.cloudApiConfig.accountId"
#     value = var.prefect_cloud_account_id
#   }

#   set {
#     name  = "agent.cloudApiConfig.workspaceId"
#     value = var.prefect_cloud_workspace_id
#   }

#   set {
#     name  = "agent.cloudApiConfig.apiKeySecret.name"
#     value = var.api_key_secret.secret_name
#   }

#   set {
#     name  = "agent.cloudApiConfig.apiKeySecret.key"
#     value = var.api_key_secret.secret_key
#   }

#   depends_on = [
#     kubernetes_namespace.prefect,
#     kubernetes_secret.prefect_api_key
#   ]
# }
