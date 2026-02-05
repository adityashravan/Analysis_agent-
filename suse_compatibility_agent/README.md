# SUSE Linux OS Compatibility Engineer

This tool uses the mino.ai API to analyze SUSE Linux OS version upgrades and their impact on Kubernetes workloads.

## Features

- Analyzes OS version changes between SUSE Linux Enterprise Server versions
- Identifies breaking and behavioral changes
- Maps OS changes to Kubernetes components
- Provides mitigation steps and recommendations
- Outputs machine-readable JSON format

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. The API key is already configured in `.env` file (not committed to git)

## Usage

### Basic Usage

```python
from suse_k8s_analyzer import SUSECompatibilityAnalyzer

# Initialize analyzer
analyzer = SUSECompatibilityAnalyzer()

# Analyze an OS upgrade
result = analyzer.analyze_os_upgrade(
    from_version="SLES 12 SP5",
    to_version="SLES 15 SP4",
    workload_type="Kubernetes"
)

# Save results
analyzer.save_analysis(result, "my_analysis.json")
```

### Run the Example

```bash
python suse_k8s_analyzer.py
```

## Output Format

The tool returns a JSON structure containing:

- **upgrade**: Source and target version information
- **breaking_changes**: List of breaking or behavioral OS changes
- **kubernetes_impact**: Impact on specific K8s components
- **mitigation_steps**: Recommended actions with priorities
- **recommendations**: General upgrade recommendations

## Architecture

The tool acts as a Senior Linux OS Compatibility Engineer specializing in:
- SUSE Linux Enterprise Server internals
- Kubernetes node requirements
- Kernel and cgroups behavior

It analyzes:
- Kernel version changes
- cgroups v1 vs v2 transitions
- systemd modifications
- Container runtime compatibility
- Networking stack changes
- Storage subsystem updates

## Security

- API key is stored in `.env` file
- `.env` is excluded from version control via `.gitignore`
- Never commit API keys to git
