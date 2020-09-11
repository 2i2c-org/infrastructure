provider "azurerm" {
  # whilst the `version` attribute is optional, we recommend pinning to a given version of the Provider
  version = "=2.20.0"
  features {}
}

terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state"
    storage_account_name = "utorontoterraformstate"
    container_name       = "terraformstate"
    key                  = "prod.terraform.tfstate"
  }
}


provider "local" {
  version = "1.4.0"
}

resource "azurerm_resource_group" "jupyterhub" {
  name     = "${var.prefix}-rg"
  location = var.region
}

resource "azurerm_virtual_network" "jupyterhub" {
  name                = "${var.prefix}-network"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name
  address_space       = ["10.0.0.0/8"]
}

resource "azurerm_subnet" "node_subnet" {
  name                 = "${var.prefix}-node-subnet"
  virtual_network_name = azurerm_virtual_network.jupyterhub.name
  resource_group_name  = azurerm_resource_group.jupyterhub.name
  address_prefixes     = ["10.1.0.0/16"]
}

resource "azurerm_kubernetes_cluster" "jupyterhub" {
  name                = "${var.prefix}-cluster"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name
  dns_prefix          = "${var.prefix}-cluster"

  linux_profile {
    admin_username = "hubadmin"
    ssh_key {
      key_data = file("${path.module}/ssh-key.pub")
    }
  }
  # Core node-pool
  default_node_pool {
    name                = "core"
    node_count          = 1
    # Unfortunately, changing anything about VM type / size recreates *whole cluster
    vm_size             = var.core_vm_size
    os_disk_size_gb     = 100
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 8
    vnet_subnet_id      = azurerm_subnet.node_subnet.id
    node_labels = {
      "hub.jupyter.org/pool-name" = "core-pool"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    # I don't trust Azure CNI
    network_plugin = "kubenet"
    network_policy = "calico"
  }

  tags = {
    Environment = "Production"
    ManagedBy   = "2i2c"
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "user_pool" {
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.jupyterhub.id
  vm_size               = var.user_vm_size
  node_count            = 1
  enable_auto_scaling   = true
  os_disk_size_gb       = 200
  node_taints           = ["hub.jupyter.org_dedicated=user:NoSchedule"]
  vnet_subnet_id        = azurerm_subnet.node_subnet.id
  node_labels = {
    "hub.jupyter.org/pool-name" = "user-alpha-pool"
  }

  min_count = 1
  max_count = 100
  tags = {
    Environment = "Production"
    ManagedBy   = "2i2c"
  }
}

# NFS VM
resource "azurerm_network_interface" "nfs_vm" {
  name                = "${var.prefix}-nfs-vm-inet"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.node_subnet.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_network_security_group" "nfs_vm" {
  name                = "${var.prefix}-nfs-vm-nsg"
  location            = azurerm_resource_group.jupyterhub.location
  resource_group_name = azurerm_resource_group.jupyterhub.name

  # SSH from the world
  security_rule {
    access                     = "Allow"
    direction                  = "Inbound"
    name                       = "ssh"
    priority                   = 100
    protocol                   = "Tcp"
    source_port_range          = "*"
    source_address_prefix      = "*"
    destination_port_range     = "22"
    destination_address_prefix = azurerm_network_interface.nfs_vm.private_ip_address
  }

  # NFS from internal network
  security_rule {
    access                     = "Allow"
    direction                  = "Inbound"
    name                       = "nfs"
    priority                   = 101
    protocol                   = "Tcp"
    source_port_range          = "*"
    source_address_prefix      = "*"
    destination_port_range     = "2049"
    destination_address_prefix = azurerm_network_interface.nfs_vm.private_ip_address
  }
}

resource "azurerm_network_interface_security_group_association" "main" {
  network_interface_id      = azurerm_network_interface.nfs_vm.id
  network_security_group_id = azurerm_network_security_group.nfs_vm.id
}

resource "azurerm_linux_virtual_machine" "nfs_vm" {
  name                = "${var.prefix}-nfs-vm"
  resource_group_name = azurerm_resource_group.jupyterhub.name
  location            = azurerm_resource_group.jupyterhub.location
  size                = var.nfs_vm_size
  admin_username      = "hubadmin"

  network_interface_ids = [
    azurerm_network_interface.nfs_vm.id,
  ]

  admin_ssh_key {
    username   = "hubadmin"
    public_key = file("${path.module}/ssh-key.pub")
  }

  os_disk {
    caching              = "None"
    storage_account_type = "StandardSSD_LRS"
    disk_size_gb         = 100
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts"
    version   = "latest"
  }
}

resource "azurerm_managed_disk" "nfs_data_disk_1" {
  name                 = "${var.prefix}-nfs-data-disk-1"
  location             = azurerm_resource_group.jupyterhub.location
  resource_group_name  = azurerm_resource_group.jupyterhub.name
  storage_account_type = "Premium_LRS"
  create_option        = "Empty"
  disk_size_gb         = "200"

  lifecycle {
    # Terraform plz never destroy data thx
    prevent_destroy = true
  }
  tags = {
    Environment = "Production"
  }
}

resource "azurerm_virtual_machine_data_disk_attachment" "nfs_data_disk_1" {
  virtual_machine_id = azurerm_linux_virtual_machine.nfs_vm.id
  managed_disk_id    = azurerm_managed_disk.nfs_data_disk_1.id
  lun                = 0
  caching            = "None"
}

locals {
  ansible_hosts = {
    "nfs_servers" = {
      hosts = {
        (azurerm_linux_virtual_machine.nfs_vm.name) = {
          ansible_ssh_common_args      = "-o ProxyCommand='./proxycommand.py %h %p'"
          ansible_user                 = "hubadmin"
          ansible_ssh_private_key_file = "../secrets/ssh-key.unsafe"
        }
      }
      "vars" = {
        disk_name = (azurerm_managed_disk.nfs_data_disk_1.name)
        disk_lun  = (azurerm_virtual_machine_data_disk_attachment.nfs_data_disk_1.lun)
      }
    }
  }
}

resource "local_file" "ansible_hosts_file" {
  content  = yamlencode(local.ansible_hosts)
  filename = "ansible-hosts.yaml"
}

output "kubeconfig" {
  value = azurerm_kubernetes_cluster.jupyterhub.kube_config_raw
}
