variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "cidr_range" {
  type    = string
  default = "10.10.0.0/24"
}
