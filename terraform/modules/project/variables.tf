variable "project_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "org_id" {
  type = string
}

variable "tf_remote_storage_buckets" {
  type = list(string)

}
variable "billing_account" {
  type = string
}
