# Company SUSE Linux Enterprise Server (SLES) Policy

## Approved Operating System Versions

| Environment | OS Version | Support Status | EOL Date |
|-------------|-----------|----------------|----------|
| Production | SLES 15 SP6 | ✅ Active | 2028-12-31 |
| Development | SLES 15 SP7 | ✅ Active | 2029-12-31 |
| Legacy | SLES 15 SP5 | ⚠️ Extended | 2027-06-30 |
| Test | SLES 15 SP7 | ✅ Active | 2029-12-31 |

## Security Hardening Requirements

### Mandatory Security Settings

1. **SELinux/AppArmor**:
   - AppArmor MUST be enabled in enforce mode
   - Custom profiles required for all production workloads

2. **Firewall**:
   - firewalld MUST be enabled
   - Only required ports opened
   - Default zone: drop

3. **SSH Configuration**:
   - PermitRootLogin: no
   - PasswordAuthentication: no (keys only)
   - Protocol: 2 only

### Kernel Parameters

Required sysctl settings for Kubernetes nodes:
```
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
vm.max_map_count = 262144
fs.inotify.max_user_watches = 524288
```

## Package Management Policy

### Approved Repositories

1. SUSE official repositories only
2. Company internal mirror (mirror.company.com)
3. SUSE Package Hub (for approved packages only)

### Prohibited Actions

- Installing packages from third-party sources
- Using pip/npm for system-level dependencies
- Compiling software from source (without approval)

## Upgrade Procedures

### SLES Service Pack Upgrades

1. **Approval Required**: Change Advisory Board (CAB)
2. **Maintenance Window**: Scheduled quarterly
3. **Testing Period**: 2 weeks in dev/test
4. **Rollback Time**: 2 hours maximum

### Known Issues - SLES 15 SP7

1. **OpenLDAP Removal**: Replaced by 389 Directory Server
   - All LDAP integrations must be migrated
   - Authentication systems need reconfiguration

2. **SMT Removal**: Replaced by RMT (Repository Mirroring Tool)
   - Repository management must migrate to RMT
   - Registration endpoints change

3. **Python 3.11**: Default Python version updated
   - Application compatibility testing required
   - Virtual environments recommended

---
Document Version: 1.5
Last Updated: 2026-01-20
