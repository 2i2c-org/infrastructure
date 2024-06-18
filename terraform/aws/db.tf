data "aws_subnets" "cluster_subnets" {
  count = var.db_enabled ? 1 : 0

  filter {
    name   = "vpc-id"
    values = [data.aws_eks_cluster.cluster.vpc_config[0]["vpc_id"]]
  }

  filter {
    name   = "tag:aws:cloudformation:logical-id"
    values = ["SubnetPublic*"]
  }
}

resource "aws_security_group" "db" {

  count = var.db_enabled ? 1 : 0

  name        = "db"
  description = "Allow traffic into the db"
  vpc_id      = data.aws_eks_cluster.cluster.vpc_config[0]["vpc_id"]
  tags        = var.tags

  ingress {
    to_port          = 3306
    from_port        = 3306
    protocol         = "tcp"
    security_groups  = [data.aws_security_group.cluster_nodes_shared_security_group.id]
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "tcp"
    security_groups  = [data.aws_security_group.cluster_nodes_shared_security_group.id]
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]

  }
}

resource "aws_db_subnet_group" "db" {
  count = var.db_enabled ? 1 : 0

  subnet_ids = data.aws_subnets.cluster_subnets[0].ids

  tags = var.tags
}

resource "aws_db_instance" "db" {

  count = var.db_enabled ? 1 : 0

  instance_class         = var.db_instance_class
  allocated_storage      = var.db_storage_size
  engine                 = var.db_engine
  engine_version         = var.db_engine_version
  identifier             = var.db_instance_identifier
  username               = "root"
  password               = random_password.db_root_password[0].result
  db_subnet_group_name   = aws_db_subnet_group.db[0].name
  vpc_security_group_ids = [aws_security_group.db[0].id]
  publicly_accessible    = true
  skip_final_snapshot    = true
  apply_immediately      = true
  availability_zone      = var.cluster_nodes_location
  parameter_group_name   = aws_db_parameter_group.db[0].name

  tags = var.tags
}

resource "aws_db_parameter_group" "db" {
  count  = var.db_enabled ? 1 : 0
  name   = var.db_instance_identifier
  family = "${var.db_engine}${var.db_engine_version}"
  tags   = var.tags

  dynamic "parameter" {
    for_each = var.db_params
    content {
      name  = parameter.key
      value = parameter.value
    }
  }
}

resource "random_password" "db_root_password" {
  count = var.db_enabled ? 1 : 0
  # mysql passwords can't be longer than 41 chars lololol
  length = 41
}

resource "random_password" "db_readonly_password" {
  count   = var.db_enabled ? 1 : 0
  special = var.db_user_password_special_chars
  # mysql passwords can't be longer than 41 chars lololol
  length = 41
}

provider "mysql" {
  # We only want to set this up if db is enabled, otherwise there is no
  # mysql endpoint for this provider to connect to. These are all still 'required'
  # parameters, so we set them to empty whenever possible. endpoint is validated to be
  # not an empty string, so we set it to "does-not-exist"
  endpoint = var.db_enabled ? aws_db_instance.db[0].endpoint : "does-not-exist"

  username = var.db_enabled ? aws_db_instance.db[0].username : ""
  password = var.db_enabled ? random_password.db_root_password[0].result : ""
}

resource "mysql_user" "user" {
  count = var.db_enabled && var.db_engine == "mysql" ? 1 : 0

  user               = "dbuser"
  host               = "%"
  plaintext_password = random_password.db_readonly_password[0].result
}

resource "mysql_grant" "user" {
  count = var.db_enabled && var.db_engine == "mysql" ? 1 : 0

  user       = mysql_user.user[0].user
  host       = "%"
  database   = "*"
  privileges = var.db_mysql_user_grants

}

output "db_helm_config" {
  value = var.db_enabled ? yamlencode({
    "jupyterhub" : {
      "custom" : {
        "singleuserAdmin" : {
          "extraEnv" : {
            "MYSQL_ROOT_USERNAME" : aws_db_instance.db[0].username,
            "MYSQL_ROOT_PASSWORD" : random_password.db_root_password[0].result
          }
        }
      }
      "singleuser" : {
        "extraFiles" : {

          "my-cnf" : {
            "mountPath" : "/home/jovyan/.my.cnf",
            "stringData" : format(
              "[client]\nhost='%s'\nuser='%s'\npassword='%s'",
              aws_db_instance.db[0].address,
              mysql_user.user[0].user,
              random_password.db_readonly_password[0].result
            )
          }
        },
        "extraEnv" : {
          "MYSQL_HOST" : aws_db_instance.db[0].address,
          "MYSQL_USERNAME" : mysql_user.user[0].user
          "MYSQL_PASSWORD" : random_password.db_readonly_password[0].result
        },
      }
    }
  }) : ""
  sensitive = true
}
