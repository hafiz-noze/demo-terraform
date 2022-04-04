variable "project_id" {
  type = "string"
  description = "The project ID to host the cluster in"
}

variable "region" {
  type = "string"
  description = "The region to host the cluster in"
  default = "us-central1"
}

variable "cluster_name" {
  type = "string"
  default = "demo-hafizur"
  description = "The name of the cluster"
}

variable "env_name" {
  type = "string"
  default = "dev"
  description = "The name env type of the cluster"
}

variable "network" {
  type = "string"
  default = "demo-nw"
  description = "The name of the network"
  
}

variable "subnetworks" {
  description = "The subnetwork created to host the cluster"
  default = "gke-subnet"
}

variable "ip_range_pods_name" {
  type = "string"
  default = "demo-ip-range-pods"
  description = "The name of the ip range for pods"
  
}

variable "ip_range_services_name" {
  type = "string"
  default = "demo-ip-range-services"
  description = "The name of the ip range for services"
  
  
}