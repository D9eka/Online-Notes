variable "yc_token" {
  type        = string
  description = "Yandex Cloud OAuth token"
}

variable "yc_cloud_id" {
  type        = string
  description = "Yandex Cloud ID"
}

variable "yc_folder_id" {
  type        = string
  description = "Yandex Folder ID"
}

variable "db_user" {
  type    = string
  default = "barchaninov"
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = "barchaninov"
}

variable "db_name" {
  type    = string
  default = "notes"
}

variable "aws_endpoint_url" {
  type    = string
  default = "https://storage.yandexcloud.net"
}

variable "aws_bucket_name" {
  type    = string
  default = "notes-files"
}

variable "aws_region_name" {
  type    = string
  default = "ru-central1"
}

variable "secret_key" {
  type      = string
  sensitive = true
  default   = "barchaninov"
}

variable "algorithm" {
  type    = string
  default = "HS256"
}

variable "access_token_expire_minutes" {
  type    = number
  default = 30
}

variable "frontend_dir" {
  type    = string
  default = "./frontend"
}

variable "vm_image_id" {
  type        = string
  description = "Base image ID for VMs"
  default     = "fd827b91d99psvq5fjit"
}

variable "docker_image" {
  type    = string
  default = "your-docker-image"
}

variable "ssh_public_keys" {
  type        = list(string)
  description = "List of public SSH keys for VM access"
  default     = []
}