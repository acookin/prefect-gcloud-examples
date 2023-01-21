resource "google_project" "my_project" {
  name            = var.project_name
  project_id      = var.project_id
  org_id          = var.org_id
  billing_account = var.billing_account
}

resource "google_project_service" "project" {
  for_each = toset(local.enabled_services)
  project  = var.project_id
  service  = each.key

  disable_dependent_services = true
}

resource "random_id" "bucket_suffix" {
  # use same bucket suffix so we know the prefixes are unique
  byte_length = 8
}

resource "google_storage_bucket" "tfremote" {
  for_each      = toset(var.tf_remote_storage_buckets)
  project       = var.project_id
  name          = "${each.key}-${random_id.bucket_suffix.hex}"
  force_destroy = false
  location      = "US"
  storage_class = "STANDARD"
  versioning {
    enabled = true
  }
}
