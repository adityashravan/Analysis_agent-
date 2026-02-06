# Company Kubernetes Policy Document

## Supported Kubernetes Versions

This document outlines the official Kubernetes versions supported for each product in our portfolio.

| Product | Kubernetes Version | Container Runtime | Support Status | Notes |
|---------|-------------------|-------------------|----------------|-------|
| Product A (Production) | 1.28.x | containerd 1.7.x | Active | Primary production workload |
| Product B (Legacy) | 1.27.x | containerd 1.6.x | LTS Support | Extended support until 2027 |
| Product C (Development) | 1.29.x | containerd 1.7.x | Beta | New development environment |
| Product D (Edge) | 1.28.x | CRI-O 1.28 | Active | Edge computing deployments |

## Container Runtime Requirements

All production Kubernetes clusters MUST use:

1. **Container Runtime**: containerd version 1.6.x or higher
   - CRI-O is approved for edge deployments only
   - Docker is deprecated and NOT supported

2. **Cgroups Configuration**:
   - cgroups v2 MUST be enabled on SLES 15 SP6+
   - systemd cgroup driver is REQUIRED
   - cgroupfs driver is NOT permitted in production

3. **Resource Limits**:
   - All pods MUST have resource requests and limits defined
   - Memory overcommit ratio: 1.5x maximum
   - CPU overcommit ratio: 2x maximum

## Operating System Compatibility Matrix

| Kubernetes Version | SLES 15 SP5 | SLES 15 SP6 | SLES 15 SP7 |
|-------------------|-------------|-------------|-------------|
| 1.26.x | ✅ Supported | ✅ Supported | ❌ Not Tested |
| 1.27.x | ✅ Supported | ✅ Supported | ⚠️ Testing Required |
| 1.28.x | ⚠️ Limited | ✅ Supported | ✅ Supported |
| 1.29.x | ❌ Not Supported | ✅ Supported | ✅ Supported |
| 1.30.x | ❌ Not Supported | ⚠️ Beta | ✅ Supported |

### Notes on Compatibility:
- SLES 15 SP7 introduces new systemd features that require Kubernetes 1.28+
- SLES 15 SP7 default cgroups v2-only mode requires container runtime updates
- OpenLDAP removal in SP7 affects LDAP-based authentication - migrate to 389-DS

## Critical Configuration Files

The following configuration files MUST be backed up before any OS upgrade:

### Kubernetes Control Plane
- `/etc/kubernetes/manifests/*.yaml` - Static pod manifests
- `/etc/kubernetes/admin.conf` - Admin kubeconfig
- `/etc/kubernetes/kubelet.conf` - Kubelet kubeconfig
- `/etc/kubernetes/controller-manager.conf` - Controller manager config
- `/etc/kubernetes/scheduler.conf` - Scheduler config

### Kubelet Configuration
- `/var/lib/kubelet/config.yaml` - Kubelet runtime configuration
- `/etc/sysconfig/kubelet` - Kubelet service configuration
- `/etc/systemd/system/kubelet.service.d/` - Systemd drop-ins

### Container Runtime
- `/etc/containerd/config.toml` - containerd configuration
- `/etc/crio/crio.conf` - CRI-O configuration (if used)
- `/etc/containers/registries.conf` - Container registries

### Networking
- `/etc/cni/net.d/*.conflist` - CNI configuration
- `/etc/calico/` - Calico configuration (if used)
- `/etc/cilium/` - Cilium configuration (if used)

## Upgrade Policy and Procedures

### Pre-Upgrade Requirements

1. **Version Constraints**:
   - Never skip more than 2 Service Pack versions
   - Kubernetes minor version must be validated against new OS
   - Container runtime version must be compatible

2. **Backup Requirements**:
   - Full etcd backup (snapshot + WAL)
   - All configuration files listed above
   - Persistent Volume data
   - Custom Resource Definitions

3. **Cluster State**:
   - All nodes must be in Ready state
   - No pending PodDisruptionBudgets violations
   - All DaemonSets must be healthy

### During Upgrade

1. **Node Drain Process**:
   ```bash
   kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
   ```

2. **Upgrade Order**:
   - Control plane nodes first (one at a time)
   - Worker nodes (rolling upgrade with max 25% unavailable)
   - Storage nodes last

3. **Health Checks**:
   - API server responding
   - etcd cluster healthy
   - All system pods running

### Post-Upgrade Validation

1. **Cluster Health**:
   ```bash
   kubectl get nodes
   kubectl get pods -A
   kubectl cluster-info
   ```

2. **Component Versions**:
   ```bash
   kubectl version
   kubelet --version
   containerd --version
   ```

3. **Workload Verification**:
   - Test application deployments
   - Verify persistent storage
   - Check network policies
   - Validate ingress/egress

## Rollback Plan

1. **Snapshot Restoration**:
   - All nodes must have pre-upgrade snapshots available
   - Restoration SLA: 4 hours maximum

2. **Kernel Rollback**:
   - Previous kernel must remain in GRUB menu
   - grub2-once can be used for single-boot rollback

3. **etcd Restoration**:
   ```bash
   etcdctl snapshot restore <snapshot-file>
   ```

## Contact and Escalation

- Platform Team: platform-team@company.com
- On-Call: +1-XXX-XXX-XXXX
- Slack: #kubernetes-support

---
Document Version: 2.1
Last Updated: 2026-01-15
Next Review: 2026-07-15
