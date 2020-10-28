# 2020-08-28 - Memory overload on WER cluster

## Summary

On 2020-08-28, WER reported [stuck pages](https://github.com/2i2c-org/pilot/issues/27) for students. A total outage, nothing usable.

After investigation, we determined that the core pods didn't have appropriate resource guarantees set. There was also no dedicated core pool, so the WER students overloaded CPU & RAM of the nodes. This starved everything of resources, causing issues.

This was resolved by:

1. Giving core pods [more resource guarantees](https://github.com/2i2c-org/pilot-hubs/commit/88767d85c306784754560dedc1d5ac7abdb8a2a0)
2. [Removing memory overcommit](https://github.com/2i2c-org/pilot-hubs/pull/88) for WER students, since they seem to be using a good chunk of their memory limit.

## Timeline

All times in IST

### 08:52 PM

Incoming report that many students can not access the hub, and it is [frozen](https://github.com/2i2c-org/pilot/issues/27#issue-731543843)

### 09:02 PM

Activity bump [is noticed](https://github.com/2i2c-org/pilot/issues/27#issuecomment-718014094) but regular
fixes (incognito, restarting servers, etc) don't seem to fix things

### 09:21 PM

Looking at resource utilization on the nodes, resource exhaustion is clear


```bash
$ kubectl top node                                                                   
NAME                                                 CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%   
gke-low-touch-hubs-cluster-core-pool-b7edea69-00sc   220m         11%    6151Mi          58%       
gke-low-touch-hubs-cluster-core-pool-b7edea69-gwrg   1944m        100%   10432Mi         98%       
```

There were only core nodes - no separate user nodes. The suspicion is that the user pods are using up just enough resources that the core pods are being starved.

### 09:23 PM

Based on [tests on how much RAM WER needs](https://github.com/2i2c-org/pilot/issues/15), we had set a limit of 2G but guarantee of only 512M - a 4x overcommit as we often do. However, the tests revealed that users almost always use just under 1G of RAM, so our overcommit should've been just 2x. We just [remove overcommit](https://github.com/2i2c-org/pilot-hubs/pull/88) for now. This will also probably spawn another node, thus easing pressure on the other existing nodes.

### 09:24 PM

We [bump resource guarantees](https://github.com/2i2c-org/pilot-hubs/commit/88767d85c306784754560dedc1d5ac7abdb8a2a0) for all the core pods as well, so they will have enough to operate even if the nodes get full. This restarts the pods, and moves some to a new node - which also helps. Things seem to return to normal.

### 09:46 PM

The [issue is closed](https://github.com/2i2c-org/pilot/issues/27#issuecomment-718044571) and everything seems fine

## Action Items

- Make sure user pods are in a separate pool, so they do not create pressure on the core pods <https://github.com/2i2c-org/pilot-hubs/issues/89>
- Set limits on the support infrastructure (prometheus, grafana, ingress) as well <https://github.com/2i2c-org/pilot-hubs/issues/90>
- Document and think about overcommit ratios for memory usage <https://github.com/2i2c-org/pilot-hubs/issues/91>
- Setup better Grafana dashboards to monitor resource usage <https://github.com/2i2c-org/pilot-hubs/issues/92>
- Document how folks can get `kubectl` access to the cluster, so others can look into issues too <https://github.com/2i2c-org/pilot-hubs/issues/87>
