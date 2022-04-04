provider "google" {
    project = "Noze"
    region = "us-central1"
}

module "gke_auth" {
    source = "terraform-google-modules/kubernetes-engine/google//modules/auth"
    depends_on = [
        module.gke
    ]
    project_id = var.project_id
    location = var.gke.location
    cluster_name = var.gke.cluster_name
}
  
resource "local_file" "kubeconfig" {
    content = module.gke_auth.kubeconfig_raw
    filename = "kubeconfig-${var.env_name}"
}

module "gcp-network" {
    source = "terraform-google-modules/network/google"
    project_id = var.project_id
    network_name = "${var.network}-${var.env_name}"
    subnetworks = [
        {
            subnet_name = "${var.subnetworks}-${var.env_name}"
            subnet_id = "10.10.0.0/16"
            subnet_region = var.region
        },
    ]

    secondary_ranges = {
        "${var.subnetwork}-${var.env_name}" = [
            {
                range_name = var.ip_range_pods_name
                ip_cidr_range = "10.20.0.0/16"
    },
            {
                range_name = var.ip_range_services_name
                ip_cidr_range = "10.30.0.0/16"
            },
        ]
    }
}

module "gke" {
    source = "terraform-google-modules/kubernetes-engine/google//modules/private-cluster"
    project_id = var.project_id
    name = "${var.cluster_name}-${var.env_name}"
    regional = true
    region = var.region
    network = module.gcp-network.network_name
    subnetwork =  var.gcp-network.subnetworks[0]
    ip_range_pods = var.ip_range_pods_name
    ip_range_services = var.ip_range_services_name
    node_pools = [
        {
            name = "node-pool"
            machine_type = "n1-standard-4"
            accelerators = [
                {
                    accelerator_type = "nvidia-tesla-t4"
                    accelerator_count = 1
                }
            ]
            scopes = [
                "https://www.googleapis.com/auth/devstorage.read_only",
                "https://www.googleapis.com/auth/logging.write",
                "https://www.googleapis.com/auth/monitoring",
                "https://www.googleapis.com/auth/servicecontrol",
                "https://www.googleapis.com/auth/service.management.readonly",
                "https://www.googleapis.com/auth/trace.append",
            ]
            disk_size_gb = 100
            num_nodes = 4
            preemptible = false
        },
    ]
    

}