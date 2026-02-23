variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "api_image" {
  type = string
}

variable "ui_image" {
  type = string
}

variable "db_url_secret_name" {
  type = string
}

variable "service_account_email" {
  type = string
}
