terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.49.0"
    }
  }
  backend "gcs" {
    bucket = "dev-project-tfstate-801f1993e9b2f506"
    prefix = "state/dev/gke/"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "gke" {
  source = "../../../modules/gke"

  vpc_name    = var.vpc_name
  subnet_name = var.subnet_name
  project_id  = var.project_id
  region      = var.region
}
