# What exactly do cloud providers charge us for?

There are a million ways to pay cloud providers money, and trying to
understand it all is [several][book-1] [books][book-2] [worth][book-3] [of][book-4] [material][book-5].

However, a lot of JupyterHub (+ optionally Dask) clusters operate in
similar ways, so we can focus on a smaller subset of ways in which cloud
companies charge us.

This document is designed not to be comprehensive, but to provide a
baseline understanding of *things in the cloud that cost money* so we can
have a baseline to reason from.

## Nodes / Virtual Machines

The unit of *compute* in the cloud is a virtual machine (a
[node](https://kubernetes.io/docs/concepts/architecture/nodes/) in
kubernetes terminology). It is assembled from the following
components:

1. CPU (count and architecture)
2. Memory (only capacity)
3. Boot disk (size and type, ephemeral)
4. Optional accelerators (like GPUs, TPUs, network accelerators, etc)

Let's go through each of these components, and then talk about how they
get combined.

### CPU

CPU specification for a node is three components:

1. Architecture ([x86_64 / amd64](https://en.wikipedia.org/wiki/X86-64) or [arm64 or aarch64](https://en.wikipedia.org/wiki/AArch64))
2. Make (Intel vs AMD vs cloud provide made ARM processor, what year the CPU was released, etc)
3. Count (total number of processors in the node)

The 'default' everyone assumes is x86_64 for architecture, and some sort of
recent intel processor for make. So if someone says 'I want 4 CPUs', we can
currently assume they mean they want 4 x86_64 Intel CPUs. x86_64 intel
CPUs are also often the most expensive - AMD CPUs are cheaper, ARM CPUs are
cheaper still. So it's a possible place to make cost differences - *but*,
some software may not work correctly on different CPUs. While ARM support
has gotten a lot better recently, it's still not on par with x86_64 support,
particularly in scientific software - see [this issue](https://github.com/pangeo-data/pangeo-docker-images/issues/396)
for an example. AMD CPUs, being x86_64, are easier to switch to for cost
savings, but may still cause issues - see [this blog post](https://words.yuvi.in/post/pre-compiling-julia-docker/)
for how the specifics of what CPU are being used may affect some software. So
these cost savings are possible, but require work and testing.

Count thus becomes the most common determiner of how much the CPU component
of a node costs for our usage pattern.

### Memory

Unlike CPU, memory is simpler - capacity is what matters. A GB of memory is a GB
of memory! We pay for how much memory capacity the VM we request has, regardless
of whether we use it or not.

### Boot disk (ephemeral)

Each node needs some disk space that lives only as long as the node is up,
to store:

1. The basic underlying operating system that runs the node itself (Ubuntu,
   [COS](https://cloud.google.com/container-optimized-os/docs) or similar)
2. Storage for any docker images that need to be pulled and used on the node
3. Temporary storage for any changes made to the *running containers* in a
   pod. For example, if a user runs `pip install` or `conda install` in a
   user server, that will install additional packages into the container
   *temporarily*. This will use up space in the node's disk as long as the
   container is running.
4. Temporary storage for logs
5. Any [emptyDir](https://kubernetes.io/docs/concepts/storage/volumes/#emptydir)
   volumes in use on the node. These volumes are deleted when the pod using
   them dies, so are temporary. But while they are in use, there needs to
   be 'some place' for this directory to live, and it is on the node's
   ephemeral disk
6. For *ephemeral hubs*, their home directories are also stored using the
   same mechanism as (3) - so they take up space on the ephemeral disk as
   well. Most hubs have a *persistent* home directory set up, detailed
   in the [Home directories section](topic:billing:resources:home).


These disks can be fairly small - 100GB at the largest, but we can get away
with far smaller disks most of the time. The performance of these disks
*primarily* matters during initial docker image pull time - faster the
disk, faster it is to pull large docker images. But it can be really
expensive to make the base disks super fast SSDs, so often a balanced
middling performance tier is more appropriate.

### Accelerators (GPU, etc)

Accelerators are a form of [co-processor](https://en.wikipedia.org/wiki/Coprocessor) -
dedicated hardware that is more limited in functionality than a general
purpose CPU, but much, *much* faster. [GPU](https://en.wikipedia.org/wiki/Graphics_processing_unit)
are the most common ones in use today, but there are also [TPU](https://cloud.google.com/tpu?hl=en)s,
[FGPA](https://en.wikipedia.org/wiki/Field-programmable_gate_array)s
available in the cloud. Accelerators can often only be attached to a subset of a cloud provider's available node types, node sizes, and cloud zones.

GPUs are the most commonly used with JupyterHubs, and are often the most
expensive as well! Leaving a GPU running for days accidentally is the
second easiest way to get a huge AWS bill (you'll meet NAT / network egress, the primary culprit, later in this document). So they are usually segregated
out into their own node pool that is _exclusively_ for use by servers that need
GPUs - a [kubernetes taint](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)
is used to exclude all other user servers from those nodes. The cluster autoscaler
can stop the GPU node as soon as there are are actual GPU users, thus saving cost.

### Combining resource sizes when making a node

While you can often make 'custom' node sizes, *most commonly* you pick
one from a predefined list offered by the cloud provider ([GCP](https://cloud.google.com/compute/docs/machine-resource),
[AWS](https://aws.amazon.com/ec2/instance-types/),
[Azure](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes)).
These machine types are primarily pre-defined sets of CPU (of a particular
generation, architecture and count), RAM and optionally
an accelerator (like GPU).

For the kinds of workloads we have, usually we pick something with a high
memory to CPU ratio, as notebooks (and dask workers) tend to be mostly
memory bound, not CPU bound.

### Autoscaling makes nodes temporary

Nodes in our workloads are *temporary* - they come and go with user
needs, and get replaced when version upgrades happen. They have
names like `gke-jup-test-default-pool-47300cca-wk01` - notice
the random string of characters towards the end. The [cluster autoscaler](https://github.com/kubernetes/autoscaler/)
is the primary reason for a new node to come into existence or disappear,
along with occasional manual node version upgrades.

Since nodes are often the biggest cloud cost for communities, and the cluster
autoscaler is the biggest determiner of how / when nodes are used,
understanding its behavior is very important in understanding cloud costs.

Documentation: [GCP](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-autoscaler), [AWS](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md), [Azure](https://learn.microsoft.com/en-us/azure/aks/cluster-autoscaler?tabs=azure-cli)

(topic:billing:resources:home)=
## Home directory

By default, we provide users with a persistent, POSIX compatible filesystem mounted
under `$HOME`. This persists across user server restarts, and is used to store
code (and sometimes data).

Because this has to persist regardless of whether the user is currently active or
not, cloud providers will charge us for it regardless of whether the user is actively
using it or not. Hence, choosing what cloud products we use here becomes crucial - if
we pick something that is a poor fit, storage costs can easily dwarf everything else.

The default from [z2jh](https://z2jh.jupyter.org/en/stable/) is to use [Dynamic
Volume
Provisioning](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning/),
which sets up a *separate, dedicated* block storage device (think of it like a
hard drive) (([EBS](https://aws.amazon.com/ebs/) on AWS, [Persistent
Disk](https://cloud.google.com/persistent-disk?hl=en) on GCP and [Disk
Storage](https://azure.microsoft.com/en-us/products/storage/disks) on Azure))
*per user*. This has the following advantages:

1. Since there is one drive per user, a user filling up their disk will only affect them -
   there will be no effect on other users. This removes a failure mode associated with one
   shared drive for all users - a single user can use up so much disk space that no other
   users' server can start!
2. Performance is pretty fast, since the disks are dedicated to a single user.
3. It's incredibly easy to set up, as kubernetes takes care of everything for us.

However, it has some massive disadvantages:

1. The variance in how much users use their persistent directory is *huge*. Our observation is that *most* users
   use only a little bit of storage, and a few users use a lot of storage. By allocating the *same* amount of disk
   space to each user, a lot of it is wasted, unused space. But, we **pay** for all this unused space! Sometimes this
   means we're paying for about 90% of disk space that's unused!


That single cost related disadvantage is big enough that we **do not** use the default home directory set up
at all! Instead, we use some sort of *shared* storage - a *single* storage device is provisioned for *all* the
users on a hub, and then *subdirectories* are mounted via [NFS](https://en.wikipedia.org/wiki/Network_File_System).
This is more complicated and offers lower performance, but the *cost model* of a pooled disk is *so much cheaper*
that it is worth it.

In the past, we have done this by managing an NFS *server* manually. While cheaper on some cloud providers,
it requires specialized knowledge and maintenance. Instead, we use the following products on various
cloud providers:

1. [Elastic Filesystem](https://aws.amazon.com/efs/) (EFS) on AWS

   There is no upper limit on size, and we are charged *only for what we use*. Most ideal shared storage product.

2. [Google Filestore](https://cloud.google.com/filestore?hl=en) on GCP

   We have to specify a maximum storage capacity, **which can never be reduced**, only increased. We pay for the maximum storage capacity, regardless of what we use.

   The smallest filestore we can provision is 1TiB, which is overkill for many of our communities. But it's the best we can do on GCP.

3. [Azure Files](https://azure.microsoft.com/en-us/products/storage/files) on Azure

   We have to specify a maximum storage capacity, which can be adjusted up or down. We pay for the maximum storage capacity, regardless of what we use.


(topic:billing:resources:network-fees)=
## Network Fees

Back in the old days, 'networking' implied literally running physical
cables between multiple computers, having an [RJ45 criping tool](https://serverfault.com/questions/1048792/how-does-the-rj45-crimping-tool-work)
in your pocket, and being able to put physical tags on cables so you
could keep track of where the other end of the cable was plugged into. Changing
network configuration often meant literally unplugging the configuration
in which physical wires were plugged from one device into another, manually
logging into specific network devices and changing configuration.

When doing things 'in the cloud', while all these physical tasks still
need to be performed, we the users of the cloud are not privy to any of that.
Instead, we operate in the world of [software defined networking](https://www.cloudflare.com/learning/network-layer/what-is-sdn/) (or SDN).
The fundamental idea here is that instead of having to phsycially connect
cables around, you can define network configuration in software somehow,
and it 'just works'. Without SDN, instead of simply creating two VMs in the
same network from a web UI and expecting them to communicate with each other,
you would have to email support, and someone will have to go physically plug
in a cable from somewhere to somewhere else. Instead of being annoyed that
'new VM creation' takes 'as long as 10 minutes', you would be *happy* that
it only took 2 weeks.

Software Defined Networking is one of the core methodologies that make the
cloud as we know it possible.

Almost **every interaction in the cloud involves transmitting data over the network**.
Depending on the source and destination of this transmission, **we may get charged for it**,
so it's important to have a good mental model of how network costs work when
thinking about cloud costs.

While the overall topic of network costs in the cloud is complex, if we are only concerned
with operating JupyterHubs, we can get away with a simplified model.

### Network Boundaries

There are two primary aspects that determine how much a network
transmission costs:

1. The total amount of data transmitted
2. The **network boundaries** it crosses

(1) is fairly intuitive - the more data that is transmitted, the
more it costs. Usually, this is measured in 'GiB of data transmitted',
rather than smaller units.

(2) is determined by the **network boundaries** a data packet has to
cross from source to destination. Network boundaries can be categorized
in a million ways. But given we primarily want to model network costs,
we can consider a boundary to be crossed when:

1. The source and destination are in different zones of the same region of the cloud provider
2. The source and destination are in different regions of the same cloud provider
3. Either the source or destination is *outside* the cloud provider

If the source and destination are within the same zone, no network cost
boundaries are crossed and usually this costs no money. As a general rule,
when each boundary gets crossed, the cost of the data transmission
goes up. Within a cloud provider, transmission between regions is often
priced based on the distance between them - australia to
the US is more expensive than Canada to the US. Data transmission from within a cloud provider to outside is the most expensive, and is also often
metered by geographical location.

This also applies to data present in any *cloud services* as well, although
*sometimes* in those cases transmission is free even in a different zone in
the same region. For example, with [AWS S3 data transfer](https://aws.amazon.com/s3/pricing/) (under the 'Data Transfer' tab), accessing
S3 buckets **in the same region** is free regardless of what zone you are in.
But, with [GCP Filestore](https://cloud.google.com/filestore/pricing#network_pricing_for_traffic_between_the_client_and), you
*do* pay network fees if you are mounting it from a different zone even if
it is in the same region. So as a baseline, we should assume that any
traffic crossing network *zone* boundaries will be charged, unless explicitly
told otherwise.

Primarily, this means we should design and place services as close to each
other as possible to reduce cost.

### Ingress and Egress fees

Cloud providers in general don't want you to leave them, and tend to
enforce this lock-in by charging an [extremely high network egress cost](https://blog.cloudflare.com/aws-egregious-egress).
Like, 'bankrupt your customer because they tried to move a bucket of data from
one cloud provider to another' high egress cost. Cloudflare estimates that
in US data centers, it's [about 80x](https://blog.cloudflare.com/aws-egregious-egress) what
it actually costs the big cloud providers. The fundamental anti-competitive nature
how egress fees can hold your data 'hostage' in a cloud provider is finally causing
regulators to crack down, but only under limited circumstances (
[AWS](https://aws.amazon.com/blogs/aws/free-data-transfer-out-to-internet-when-moving-out-of-aws/),
[GCP](https://cloud.google.com/blog/products/networking/eliminating-data-transfer-fees-when-migrating-off-google-cloud)).

So when people are 'scared' of cloud costs, it's **most often** network
egress costs. It's very easy to make a bucket public, have a single other person
try to access it from another cloud provider, and get charged [a lot of money](https://2i2c.freshdesk.com/a/tickets/1105).

While scary, it's also fairly easy for us to watch out for.
A core use of JupyterHub is to put the compute near where the data is, so
*most likely* we are simply not going to see any significant egress fees
at all, as we are accessing data in the same region / zone. Object storage
access is the primary point of contention here for the kind of infrastructure
we manage, so as long as we are careful about that we should be ok. If you have data
in more than one region / zone, set up a hub in each region / zone you have data in -
move the compute to where the data is, rather than the other way around.

More information about managing this is present in the [object storage
section](topic:billing:resources:object-storage) of this guide.

(topic:billing:resources:object-storage)=
## Object storage

[Object Storage](https://en.wikipedia.org/wiki/Object_storage) is one of the
most important paradigm shifts of the 'cloud' revolution. Instead of data
being accessed as *files* via POSIX system calls (like `read`, `write`, etc),
data is stored as *objects* and accessed via HTTP methods over the network
(like `GET`, `PUT`, etc). This allows for *much* cheaper storage, and much
higher scalability at the cost of a little more complexity (as all data
access becomes a network call). While home directories may store users' code,
the data is either currently already being stored in object storage, or is
going to be stored that way in the near future.

While object storage has been around since the 90s, it was heavily
popularized by the introduction of [AWS S3](https://aws.amazon.com/s3/) in
2006. A lot of modern object storage systems are thus described as 'S3
compatible', meaning that any code that can access data from S3 can also
access data from these systems automatically.

### Storage fees, operation fees and class

When storing data in object storage, you have to select a *storage class*
first. This determines both the *latency* of your data access as well as
cost, along with some additional constraints (like minimum storage duration)
for some classes. While this can be set on a *per object* basis, usually it
is set at the *bucket* level instead.

Once you have picked your storage class, the cost associated is down to
the **amount of data stored** and the **number of operations performed** on
these objects. Amount of data stored is simple - you pay a $ amount per GB
of data stored per month.

There's a cost associated with each *operation* (GET, PUT, LIST,
etc) performed against them. Mutating and listing operations usually cost an order of magnitude more than simple read operations. But overall the fees
are not that high - on AWS, it's $0.0004 for every 1,000 read requests
and $0.005 for every 1,000 write requests. Given the patterns in which most JupyterHubs operate, this is not a big source of fees.

The cheaper it is
to *store*, the more expensive it is to *access*. The following table of costs
from S3 illustrates this - and this is not *all* the classes available!

| Class | Storage Fee | Access Fee |
| - | - | - |
| Standard | $0.023 / GB| $0.0004 / 1,000 req |
| Standard - Infrequent Access | $0.0125 / GB | $0.001 / 1,000 req |
| Glacier Deep Archive | $0.00099 / GB | $(0.0004 + 0.10) / 1,000 req + $0.02 per GB |

Picking the right storage class based on usage pattern is hence important
to optimizing cost. This is generally true for most cloud providers.
A full guide to picking storage class is out of scope for this document
though.

Pricing link: [AWS S3](https://aws.amazon.com/s3/pricing/), [GCP GCS](https://cloud.google.com/storage/pricing), [Azure Blob Storage](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/)

### Egress fees

As discussed in the [network fees
section](topic:billing:resources:network-fees), *egress* fees are how cloud
providers often lock you in. They want you to store all your data in them,
particularly in their object stores, and charge an inordinate amount of money to
take that data with you somewhere else. This is egregious enough now that
[regulators are
noticing](https://www.cnbc.com/2023/10/05/amazon-and-microsofts-cloud-dominance-referred-for-uk-competition-probe.html),
and that is probably the long term solution.

In the meantime, the answer is fairly simple - **never** expose your
object store buckets to the public internet! Treat them as 'internal' storage
only. JupyterHubs should be put in the same region as the
object store buckets they need to access, so this access can be free of cost,
even avoiding the cross-region charges.

If you *must* expose object store data to the public internet, consider
[getting an OSN Pod](https://www.openstoragenetwork.org/) (NSF funded). They
provide fully compatible object stores with zero egress fees and fairly good
performance. And perhaps, if you live in a rich enough country, let your
regulator know this is an anti-competitive practice that needs to end.

## LoadBalancers

Each cluster uses a *single* kubernetes service of [type LoadBalancer](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)
to get any HTTP(S) traffic into the cluster. This creates a single
"Load Balancer" in the cloud provider, providing us with a static IP (GCP & Azure) or CNAME (AWS) to direct our traffic into.

After traffic gets into
the cluster, it is routed to various places via kubernetes [ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
objects, backed by
the community maintained [ingress-nginx](https://github.com/kubernetes/ingress-nginx)
provider (*not* the VC backed [nginx-ingress](https://docs.nginx.com/nginx-ingress-controller/) provider). So users access JupyterHub,
Grafana, as well as any other service through this single endpoint.

Each Load Balancer costs money as long as it exists, and there is a per GB
processing charge as well. Since we don't really have a lot of data coming
*in* to the JupyterHub (as only user sessions are exposed via the browser),
the per GB charge usually doesn't add up to much (even uploading 1 terabyte of data, which will be very slow, will only cost between $5 - $14).

1. [AWS ELB](https://aws.amazon.com/elasticloadbalancing/pricing/?nc=sn&loc=3)

   We currently use [Classic Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/introduction.html) as that is the kubernetes
   default. Pricing varies by region, but is mostly $0.025 per hour + $0.008
   per GB.

2. [GCP Cloud LoadBalancing](https://cloud.google.com/vpc/network-pricing#lb)

   Pricing varies by region, but is about $0.0327 per hour per load balancer
   (listed as 'forwarding rule' in the pricing page, as our load balancers only have one forwarding rule each)
   + $0.01046 per GB processed.

3. [Azure LoadBalancer](https://azure.microsoft.com/en-us/pricing/details/load-balancer/)

   Pricing varies by region, but is about $0.025 per hour per load balancer
   (listed as a 'rule' in the pricing page, as our load balancers only have one rule each) + $0.005 per GB processed.

## Access to the external internet

Users on JupyterHubs generally expect to be able to access the external
internet, rather than only internal services. This requires one of two
solutions:

1. Each **node** of our kubernetes cluster gets an **external IP**, so
   each node has direct access to the external internet.
2. A single [Network Address Translation](https://en.wikipedia.org/wiki/Network_address_translation) (NAT)
   device is set up for the cluster, and all external traffic goes through
   this.

There are cost (and sometimes quota) considerations for either option.

### Public IP per node

If each node gets a public IP, any traffic *to* the external internet looks
like it is coming from the node. This has two cost considerations:

1. There is **no charge** for any data coming in on any of the cloud providers,
   as it is counted purely as 'data ingress'. So if a user is downloading
   terabytes of data from the public internet, it's almost completely free.
   Sending data out still costs money (as metered by 'data egress'), but
   since our usage pattern is more likely to download massive data than
   upload it, data egress doesn't amount to much in this context.

2. On some cloud providers, there is a public IP fee that adds to the
   cost of *each* node. This used to be free, but started costing money
   only recently (starting in about 2023).

   | Cloud Provider | Pricing | Link |
   | - | - | - |
   | GCP | $0.005 / hr for regular instances, $0.003 / hr for pre-emptible instances | [link](https://cloud.google.com/vpc/network-pricing#ipaddress) |
   | AWS | $0.005 / hr | [link](https://aws.amazon.com/vpc/pricing/) (see 'Public IPv4 Addresses' tab)
   | Azure | $0.004 / hr | [link](https://azure.microsoft.com/en-us/pricing/details/ip-addresses/) (Dynamic IPv4 Address for "Basic (ARM)" |

This is the *default* mode of operation for our clusters, and it mostly works
ok! We pay for each node, but do not have to worry about users racking up big
bills because they downloaded a couple terabytes of data. Since the originating IP of each network request is the *node* the user pod is on,
this also helps with external services (such as on-prem NASA data
repositories) that throttle requests based on *originating IP* - all users
on a hub are less likely to be penalized due to one user exhausting this
quota.

There are two possible negatives when using this:

1. Each of our nodes is directly exposed to the public internet, which means
   theoretically our attack surface is larger. However, these are all
   cloud managed kubernetes nodes without any real ports open to the public,
   so not a particularly large risk factor.
2. Some clouds have a separate quota system for public IPs (GCP, Azure), so this may
   limit the total size of our kubernetes cluster even if we have other
   quotas.

### Cloud NAT

The alternative to having one public IP per node is to use a [Network Address Translation](https://en.wikipedia.org/wiki/Network_address_translation)
(NAT) service. All external traffic from all nodes will go out via this
single NAT service, which usually provides a single (or a pool of) IP addresses
that this traffic looks to originate from. Our kubernetes nodes are not
exposed to the public internet at all, which theoretically adds another
layer of security as well.

```{image} https://hackmd.io/_uploads/H1IYevYi6.png)
:alt: Dr. Who Meme about Cloud NAT. One of the many memes about Cloud NAT being expensive, from [QuinnyPig](https://twitter.com/QuinnyPig/status/1357391731902341120). Many seem far more violent. See [this post](https://www.lastweekinaws.com/blog/the-aws-managed-nat-gateway-is-unpleasant-and-not-recommended/) for more information.
```

However, using a cloud NAT for outbound internet access is the **single most
expensive** thing one can do on any cloud provider, and must be avoided at all
costs. Instead of data *ingress* being free, it becomes pretty incredibly
expensive.

| Cloud Provider | Cost | Pricing Link |
| - | - | - |
| GCP | $(0.044 + 005) per hour + $0.045 per GiB | [link](https://cloud.google.com/nat/pricing) |
| AWS | $0.045 per hour + $0.045 per GiB | [link](https://aws.amazon.com/vpc/pricing/) |
| Azure | $0.045 per hour + $0.045 per GiB | [link](https://azure.microsoft.com/en-us/pricing/details/azure-nat-gateway/) |

Data *ingress* costs go from zero to $0.045 per GiB. So a user could download
a terabyte of data, and it costs about $46 instead of $0. This can escalate
real quick, because this cost is *invisible* to the user.

The shared IP also causes issues with external services that throttle per IP.

So in general **we should completely avoid using NATs**, unless forced to by
external constraints - primarily, some organizations might force a 'no public
IPs on nodes' policy. While this may be useful policy in cases where individual
users are creating individual VMs to do random things, it is counterproductive
in our set up - and only makes things expensive.

## Other Persistent Disk Storage

We use dedicated, always on block storage for the following parts of
the infrastructure:

1. The hub database

   This stores the `sqlite3` database that the JupyterHub
   process itself uses for storing user information, server information, etc.
   Since some of our hubs rely on admins explicitly adding users to the
   hub database via the hub admin, this disk is important to preserve.

   It is usually 1GiB in size, since that is the smallest disk we can get
   from many of these cloud providers. However, on *Azure*, we also store
   the hub logs on this disk for now - so the disk size is much larger.

   High performance is not a consideration here, so we usually try to use
   the cheapest (hence slowest disk) possible.

2. Prometheus disk

   We use [prometheus](https://prometheus.io/) to store time series data,
   both for operational (debugging) as well as reporting (usage metrics)
   purposes. We retain 1 year of data, and that requires some disk space.
   We try to not use the slowest disk type, but this doesn't require the
   fastest one either.

   Currently, most prometheus disks are bigger than they need to be. We
   can slim them down with effort if needed.

3. Grafana disk

   Grafana also uses a sqlite database the same way JupyterHub does. While
   most of the dashboards we use are [managed in an external repo](https://github.com/jupyterhub/grafana-dashboards),
   the database still holds user information as well as manually set up
   dashboards. This does not need to be fast, and we also try to have the
   smallest possible disk here (1GiB)

4. Optional per-user disk for dedicated databases

   One of the features we offer is a database per user, set up as a sidecar.
   Most databases do not want to use NFS as the backing disk for storing
   their data, and need a dedicated block storage device. One is created
   *for each user* (via [Kubernetes Dynamic Volume Provisioning](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning/)),
   and this can get quite expensive
   (for reasons outlined in the ["Home Directory Storage" section](topic:billing:resources:home)).

Pricing is primarily dependent on the expected disk performance (measured as throughput and IOPS) as well as the disk size. While there's a lot of
options available, we'll list what we most commonly use in this table.

| Cloud Provider | Cost | Pricing Page |
| - | - | - |
| GCP | Standard (Slow) - $0.048 / GB / month, Balanced (Most common) - $0.12 / GB / month  | [link](https://cloud.google.com/compute/disks-image-pricing#disk) |
| AWS | gp2 (most common) - $0.1 / GB / month | [link](https://aws.amazon.com/ebs/pricing/) |
| Azure | ??? | [link](https://azure.microsoft.com/en-us/pricing/details/managed-disks/) |


## Kubernetes Cluster management

Cloud providers charge for maintaining the Kubernetes cluster itself,
separate from the nodes used to run various things in it. This is usually a *fixed* per hour cost per cluster.

1. [AWS EKS](https://aws.amazon.com/eks/pricing/)

   Costs $0.10 per hour flat.

2. [GCP GKE](https://cloud.google.com/kubernetes-engine/pricing#standard_edition)

   Costs $0.10 per hour flat.

   There is a discount of about 75$ per month allowing one *zonal* (single zone,
   non highly available) cluster per GCP billing account continuously for free.
   This discount is of little value to us and communities since since we favor
   the *regional* (multi-zone, highly available) clusters for less disruptive
   kubernetes control plane upgrades, and since we don't manage that many
   separate billing accounts.

   GKE also has an 'autopilot' edition that we have tried to use in the
   past and decided against using, for various restrictions it has on
   what kind of workloads it can run.

3. [Azure AKS](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/)

   Our clusters are currently on the *Free* tier, so don't cost any money.
   Their documentation suggests this is not recommended for clusters with
   more than 10 nodes, but we've generally not had any problems with it
   so far.

## Image Registry

We primarily have people use [quay.io](https://quay.io) to store their
docker images, so usually it doesn't cost anything. However, when we have
dynamic image building enabled, we use the native container image registry
in the cloud provider we use. Usually they charge for storage based on size,
and we will have to eventually develop methods to clean unused images out
of the registry. Exposing built images publicly will subject us to big
network egress fees, so we usually do not make the built images available
anywhere outside of the region / zone in which they are built.

Pricing links: [GCP](https://cloud.google.com/artifact-registry/pricing), [AWS](https://aws.amazon.com/ecr/pricing/), [Azure](https://azure.microsoft.com/en-us/pricing/details/container-registry/)

## Logs

Logs are incredibly helpful when debugging issues, as they tell us exactly
what happened and when. The problem usually is that there's a *lot* of logs,
and they need to be stored & indexed in a way that is helpful for a human.
All the cloud providers offer some (possibly expensive) way to store and
index logs, although whether it is actually helpful for a human is up for
debate. The following resources produce logs constantly:

1. The Kubernetes control plane itself (all API requests, node joinings, etc)
2. The various system processes running on each node ([kernel ring buffer](https://man7.org/linux/man-pages/man1/dmesg.1.html),
   container runtime, mount errors / logs, systemd logs, etc)
3. Kubernetes components on each node (`kubelet`, various container runtimes, etc)
4. All kubernetes pods (we access these with `kubectl logs` while they are active, but
   the logging system is required to store them for use after the pod has been deleted)
5. [Kubernetes Events](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/event-v1/)
6. The Cluster Autoscaler (to help us understand autoscaling decisions)
7. Probably more. If you think 'this thing should have some logs', it probably does,
   if you can find it.

Google cloud has [StackDriver](https://cloud.google.com/products/operations?hl=en),
which is automatically already pre-configured to collect logs from all our clusters.
AWS supports [CloudWatch](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)
for logs, but they aren't enabled by default. Azure probably has at least one product
for logs.


[book-1]: https://www.oreilly.com/library/view/cloud-finops/9781492054610/
[book-2]: https://www.porchlightbooks.com/product/cloud-cost-a-complete-guide---2020-edition--gerardus-blokdyk?variationCode=9780655917908
[book-3]: https://www.abebooks.com/servlet/BookDetailsPL?bi=31001470420&dest=usa
[book-4]: https://www.thriftbooks.com/w/cloud-data-centers-and-cost-modeling-a-complete-guide-to-planning-designing-and-building-a-cloud-data-center_caesar-wu_rajkumar-buyya/13992190/item/26408356/?srsltid=AfmBOootnd77xklpoo2MTy8n0np1b5oamDo5KgOg9dCD-0bKody2zEF14oU#idiq=26408356&edition=14835620
[book-5]: https://bookshop.org/p/books/reduce-cloud-computing-cost-101-ideas-to-save-millions-in-public-cloud-spending-abhinav-mittal/10266848
