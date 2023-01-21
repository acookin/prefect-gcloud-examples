
terraform {
  backend "gcs" {
    bucket = "dev-project-tfstate-801f1993e9b2f506"
    prefix = "state/dev/project/"
  }
}
