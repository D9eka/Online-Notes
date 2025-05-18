output "load_balancer_ip" {
  value = yandex_lb_network_load_balancer.lb.listener[*].external_address_spec[*].address
}

output "bucket_name" {
  value = yandex_storage_bucket.bucket.bucket
}

output "postgresql_host" {
  value = yandex_mdb_postgresql_cluster.postgresql.host[0].fqdn
}