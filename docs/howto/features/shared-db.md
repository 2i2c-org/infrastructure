(features:shared-db)=
# Setup a shared database for all users on the hub

We can setup a *centralized* database that can be used by various users on the hub.
The most common use case here is to have hub admins load useful data into the
database, which is then read by various users on the hub (who only have readonly access).

(features:shared-db:aws)=
## AWS

We currently only support this on AWS, using managed [AWS RDS instances](https://aws.amazon.com/rds/). Our terraform only supports MySQL at this point, but it should be
fairly simple to port it to Postgres.

### Setting up the RDS Instance

We have a bunch of Terraform variables, prefixed with `db_` that help you control the
database instance to be set up.

```
# Enable centralized database with RDS
db_enabled = true
# Use MySQL as the engine, postgresql is also supported by RDS
db_engine = "mysql"
# Version of the database engine to use
db_engine_version = "8.0"
# Used in the hostname of the database
db_instance_identifier = "<name-of-db>"
# Size of the database disk - can be resized upwards later if needed
db_storage_size = 200
# Memory & CPU allocated to the database
db_instance_class = "db.m5.2xlarge"
# Use this to set any additional parameters to configure the db engine
db_params = {}
```

You can see more documentation for these specific variables in their descriptions
in [`aws/variables.tf`](https://github.com/2i2c-org/infrastructure/blob/HEAD/terraform/aws/variables.tf).


### Setting up a readonly user

For MySQL, we also currently support setting up a ReadOnly user whose credentials
can be distributed to non-admin user. By default, it has just enough MySQL grants to
read all contents of all databases, and nothing more. This can be adjusted with the
`db_mysql_user_grants` terraform variable. If for some reason you don't want to have
special characters in the generated password for this user, you can toggle that with
`db_user_password_special_chars`.

### Passing credentials to the hub

Once you've `terraform apply`d all the config, you can get the config that should
be passed to `helm` with `terraform output -raw db_helm_config`. This should output
YAML that should put into a `sops` encrypted secret config file specific to the hub.
This sets up a couple of environment variables (`MYSQL_ROOT_USERNAME` and
`MYSQL_ROOT_PASSWORD`) available *just* to hub admins, and a bunch more
(`MYSQL_HOST`, `MYSQL_USERNAME`, `MYSQL_PASSWORD`) available to all users.
A `.my.cnf` file will also be automatically mounted under `~/.my.cnf` for all
hub users with regular user credentials, so these credentials will be auto discovered
by most MySQL tooling!
