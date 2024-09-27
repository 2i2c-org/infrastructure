tenant_id                   = "d61ecb3b-38b1-42d5-82c4-efb2838b925c"
subscription_id             = "cde71e96-035f-4b76-84ba-23d40a61897d"
resourcegroup_name          = "2i2c-jupyterhub-prod"
global_storage_account_name = "2i2cjupyterhubstorage"
location                    = "canadacentral"
budget_alert_amount         = null
storage_size                = 512
ssh_pub_key                 = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDVwTlihyq578lR5Mp/d9dZFIRko7YglaFeux1Mq6bssfqTLqesc9xVZS5wjmNthW6yrcrbEawsF80JEzkZLUMdC3jKxmUgTU/Htf3Zf7P3N7yWa6er2alV2wX7mkTGwrRd/hKneqJEDuhnCfSWJ9U3Pyd0zM8OhCd8AMbnbR+bR0s1+bI5xWQNkV+DRaLjOA+5OoCObxZgGKGfP/2mqgmgYhWWI3K/DQPzYbX9OszLe/LjBqxcx3zEpupr+qW4A1N11I6I4le4RMcZ+PvbIswq/HxurvJMhYsAvkhP/k9TDt2KGykMZ1xmzBZ05vjr7PqeYXpJSajJVHpWVh9i8lOYLnn+PHyT2nF8JbpAsvcxxn1WzsppWX3JxTOKqhw3SlFUuPlG7Kfba/5Ms41HAwxrneLzfD3To2AG6VoG3EzVFBNviKrebAB2uLyZ7h25jEbqArbhCgDShvIxwa1VlP9vAIrios0rmpOLZ8NfIvPwkYoZU5NRKbaNQL1x0HMPWK0= sgibson@Athena.local"

kubernetes_version = "1.30.3"

node_pools = {
  core : [
    {
      name : "core",
      vm_size : "Standard_E2s_v5",
      os_disk_size_gb : 40,
      kubelet_disk_type : "OS",  # Temporary disk does not have enough space
      min : 1,
      max : 10,
    },
  ],
  user : [
    {
      name : "usere8sv5",
      vm_size : "Standard_E8s_v5",
      os_disk_size_gb : 200,
      min : 0,
      max : 100,
    },
  ],
  dask : [],
}
