provider "google" {
  project = "Noze"
}

module "gke_auth" {
  source = "../../gke_auth"
  
}