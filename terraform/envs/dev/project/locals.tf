locals {
  project_id = format("%s-%s", var.project_id_prefix, random_string.random.id)


  tf_remote_storage_buckets = [
    "dev-project-tfstate"
  ]
}
