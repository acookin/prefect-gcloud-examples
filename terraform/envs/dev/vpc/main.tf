terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.49.0"
    }
  }
  backend "gcs" {
    bucket = "dev-project-tfstate-801f1993e9b2f506"
    prefix = "state/dev/vpc/"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "vpc" {
  source = "../../../modules/vpc"

  cidr_range = var.cidr_range
  project_id = var.project_id
  region     = var.region
}
