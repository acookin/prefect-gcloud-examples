variable "gke_num_nodes" {
  default     = 1
  description = "number of gke nodes"
}

variable "vpc_name" {
  type = string
}

variable "subnet_name" {
  type = string
}

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}
