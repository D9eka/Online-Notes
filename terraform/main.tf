terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.77.0"
    }
  }
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = "ru-central1-a"
}

# VPC Network
resource "yandex_vpc_network" "network" {
  name = "notes-network"
}

# Subnets
resource "yandex_vpc_subnet" "subnet-app" {
  name           = "subnet-app"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.0.1.0/24"]
}

resource "yandex_vpc_subnet" "subnet-db" {
  name           = "subnet-db"
  zone           = "ru-central1-b"
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.0.2.0/24"]
}

resource "yandex_vpc_subnet" "subnet-public" {
  name           = "subnet-public"
  zone           = "ru-central1-a"  # Используем корректную зону
  network_id     = yandex_vpc_network.network.id
  v4_cidr_blocks = ["10.0.3.0/24"]
}

# Security Groups
resource "yandex_vpc_security_group" "db-sg" {
  name        = "db-sg"
  network_id  = yandex_vpc_network.network.id

  ingress {
    description    = "PostgreSQL"
    protocol       = "TCP"
    port           = 6432
    v4_cidr_blocks = [yandex_vpc_subnet.subnet-app.v4_cidr_blocks[0]]
  }
}

resource "yandex_vpc_security_group" "vm-sg" {
  name        = "vm-sg"
  network_id  = yandex_vpc_network.network.id

  ingress {
    description    = "HTTP"
    protocol       = "TCP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description    = "SSH"
    protocol       = "TCP"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# PostgreSQL Cluster
resource "yandex_mdb_postgresql_cluster" "postgresql" {
  name        = "notes-postgresql"
  environment = "PRESTABLE"
  network_id  = yandex_vpc_network.network.id

  config {
    version = 15
    resources {
      resource_preset_id = "s2.micro"
      disk_type_id       = "network-ssd"
      disk_size          = 10
    }
  }

  host {
    zone      = "ru-central1-b"
    subnet_id = yandex_vpc_subnet.subnet-db.id
  }

  security_group_ids = [yandex_vpc_security_group.db-sg.id]
}

# PostgreSQL User
resource "yandex_mdb_postgresql_user" "db_user" {
  cluster_id = yandex_mdb_postgresql_cluster.postgresql.id
  name       = var.db_user
  password   = var.db_password
}

# PostgreSQL Database
resource "yandex_mdb_postgresql_database" "db" {
  cluster_id = yandex_mdb_postgresql_cluster.postgresql.id
  name       = var.db_name
  owner      = yandex_mdb_postgresql_user.db_user.name
}

# Object Storage
resource "yandex_storage_bucket" "bucket" {
  bucket     = var.aws_bucket_name
  acl        = "public-read"
  folder_id  = var.yc_folder_id  # Явное указание folder_id
  access_key = yandex_iam_service_account_static_access_key.sa-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-key.secret_key
}

# Service Account
resource "yandex_iam_service_account" "sa" {
  name = "bucket-sa"
}

resource "yandex_resourcemanager_folder_iam_binding" "binding" {
  folder_id = var.yc_folder_id
  role      = "storage.editor"
  members   = ["serviceAccount:${yandex_iam_service_account.sa.id}"]
}

resource "yandex_iam_service_account_static_access_key" "sa-key" {
  service_account_id = yandex_iam_service_account.sa.id
}

# VMs
resource "yandex_compute_instance" "vm" {
  count = 2

  name        = "vm-${count.index}"
  platform_id = "standard-v3"
  zone        = "ru-central1-a"

  resources {
    cores  = 2
    memory = 2
  }

  boot_disk {
    initialize_params {
      image_id = var.vm_image_id
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.subnet-app.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.vm-sg.id]
  }

  metadata = {
    user-data = <<-EOF
      #!/bin/bash
      # Install Docker
      sudo apt-get update
      sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
      sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
      sudo apt-get update
      sudo apt-get install -y docker-ce docker-ce-cli containerd.io

      # Create .env file
      cat <<EOT > /home/ubuntu/.env
      DB_HOST=${yandex_mdb_postgresql_cluster.postgresql.host[0].fqdn}
      DB_PORT=6432
      DB_USER=${var.db_user}
      DB_PASSWORD=${var.db_password}
      DB_NAME=${var.db_name}
      AWS_ENDPOINT_URL=${var.aws_endpoint_url}
      AWS_ACCESS_KEY_ID=${yandex_iam_service_account_static_access_key.sa-key.access_key}
      AWS_SECRET_ACCESS_KEY=${yandex_iam_service_account_static_access_key.sa-key.secret_key}
      AWS_BUCKET_NAME=${var.aws_bucket_name}
      AWS_REGION_NAME=${var.aws_region_name}
      SECRET_KEY=${var.secret_key}
      ALGORITHM=${var.algorithm}
      ACCESS_TOKEN_EXPIRE_MINUTES=${var.access_token_expire_minutes}
      FRONTEND_DIR=${var.frontend_dir}
      EOT

      # Run Docker container
      sudo docker pull ${var.docker_image}
      sudo docker run -d --env-file /home/ubuntu/.env -p 80:80 ${var.docker_image}
    EOF
    ssh-keys = join("\n", [for key in var.ssh_public_keys : "ubuntu:${key}"])
  }
}

# Load Balancer
resource "yandex_lb_target_group" "tg" {
  name = "app-tg"

  dynamic "target" {
    for_each = yandex_compute_instance.vm[*].network_interface.0.ip_address
    content {
      subnet_id = yandex_vpc_subnet.subnet-app.id
      address   = target.value
    }
  }
}

resource "yandex_lb_network_load_balancer" "lb" {
  name = "app-lb"

  listener {
    name = "http-listener"
    port = 80
    external_address_spec {
      ip_version = "ipv4"
    }
  }

  attached_target_group {
    target_group_id = yandex_lb_target_group.tg.id

    healthcheck {
      name = "http"
      http_options {
        port = 80
        path = "/"
      }
    }
  }
}