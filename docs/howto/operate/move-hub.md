# Move a Hub across clusters

Moving hubs between clusters is possible, but requires manual steps
to ensure data is preserved.

1. Setup [a new hub](../../topic/config.md) in the appropriate cluster.

2. Copy home directory contents from the old cluster's NFS server to
   the new cluster's. Here is a simple method that works when the
   cluster is on its own NFS server (and not on something like EFS)

   a. In the target NFS server, create a new ssh key-pair, with
      `ssh-keygen -f nfs-transfer-key`

   b. Copy the public key `nfs-transfer-key.pub` to the source NFS
      server's `/home/ubuntu/.ssh/authorized_keys`, so the target
      NFS server can `scp` from the source NFS server.

   c. Copy the NFS home directories from the source NFS server to
      the target NFS server, making sure that the NFS exports locations
      match up appopriately. For example, if the source NFS server has
      home directories for each hub stored in `/export/home-01/homes`,
      and the target NFS server also has hub home directories stored under
      `/export/home-01/homes`, you can `scp` the contents across with:

      ```bash
      su ubuntu
      scp -p -r -i nfs-transfer-key ubuntu@nfs-source-server-public-IP:/export/home-01/homes/<hub-name> /export/home-01/homes/<hub-name>
      ```

      This makes sure the target is owned by the `ubuntu` user, which has
      uid `1000`. Our user pods run as uid `1000`, so this makes sure they
      can mount their home directories.

3. Copy `/srv/jupyterhub/jupyterhub.sqlite` file from old hub pod to new
   hub's. This preserves user information, since they might be added via
   the admin UI. The `kubectl cp` command might be used here, to copy
   `jupyterhub.sqlite` file from old hub pod to your local machine, and
   then to the new hub.

4. Move DNS from old cluster to new cluster, thus completing the move.
