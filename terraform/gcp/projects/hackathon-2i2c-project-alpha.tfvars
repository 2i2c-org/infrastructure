prefix     = "alpha"
project_id = "hackathon-2i2c-project-alpha"

enable_network_policy = true

# Inane CPU requests mean we need at least 3 CPUs for a base node?!?!
# But, we can't have custom machine sizes with odd number of CPUs -
# only even numbers. So we go with 4. 3840 is the smallest amount
# of RAM a 4 CPU n1 instance can have.
core_node_machine_type = "n1-custom-4-3840"

# Give each user ~4G of RAM and ~2CPU
user_node_machine_type = "e2-custom-2-4096"
