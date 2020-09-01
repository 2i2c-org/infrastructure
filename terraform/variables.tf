variable "prefix" {
  type = string
}

variable "project_id" {
  type = string
  # This is in Toronto!
  default = "two-eye-two-see"
}

variable "region" {
  type = string
  default = "us-central1"
}

variable "zone" {
  type = string
  default = "us-central1-b"
}