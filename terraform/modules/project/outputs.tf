output "tf_state_buckets" {
  value = flatten([
    for k, v in toset(var.tf_remote_storage_buckets) : {
      bucket_name = k
      bucket      = google_storage_bucket.tfremote[k].name
    }
  ])
}

