# OS & Kubernetes Version Impact Analysis System

**Scalable Multi-Agent Architecture with Upstream-Downstream Pattern**

A powerful, extensible AI system for analyzing version changes and their cascading impacts across technology stacks. Currently specialized for SUSE Linux and Kubernetes, but designed to scale to any technology domain.

## 🎯 What This Does

### Simple User Experience
```python
# User just provides two OS versions - that's it!
from core.orchestrator import Orchestrator

orchestrator = Orchestrator(config)
analysis = orchestrator.analyze_simple("SLES 15 SP6", "SLES 15 SP7")

# System automatically:
# 1. Analyzes OS-level changes
# 2. Identifies Kubernetes impacts
# 3. Provides mitigation steps
# 4. Can cascade to database, app, and other agents
```

### Answers Critical Questions
- **What changes between OS versions?** (e.g., SUSE 15 SP6 → SP7)
- **What breaks in Kubernetes when OS changes?**
- **What breaks in databases when OS/K8s changes?**
- **How do I mitigate each issue?**
- **What's the upgrade timeline?**

## 🏗️ Architecture

### Upstream-Downstream Pattern
```
┌──────────────────────────────────────────────────────────────────┐
│                      USER INPUT                                   │
│              "SLES 15 SP6" → "SLES 15 SP7"                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   ORCHESTRATOR  │ ◄── Manages agent registry
                    │                 │     and dependency graph
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    OS AGENT     │ ◄── ROOT AGENT
                    │   (SUSE Linux)  │     Detects OS changes
                    └────────┬────────┘
                             │
                ┏────────────┴────────────┓
                ▼                         ▼
       ┌─────────────────┐      ┌─────────────────┐
       │ KUBERNETES      │      │  DATABASE       │ ◄── DOWNSTREAM
       │ AGENT           │      │  AGENT          │     AGENTS
       │                 │      │  (Example)      │     (parallel)
       └────────┬────────┘      └─────────────────┘
                │
                ▼
       ┌─────────────────┐
       │ APPLICATION     │ ◄── Further downstream
       │ AGENT (Future)  │     agents can be added
       └─────────────────┘
```

### Key Concepts

1. **Root Agent (OS Agent)**
   - Starting point of analysis
   - Detects changes in OS layer
   - Automatically propagates to downstream agents

2. **Downstream Agents**
   - Register with upstream agents
   - Automatically receive upstream changes
   - Analyze impact in their domain
   - Can have their own downstream agents (cascading)

3. **Agent Registry**
   - Central tracking of all agents
   - Dependency graph management
   - Dynamic agent addition

4. **Automatic Cascading**
   - Changes flow automatically through the chain
   - No manual coordination needed
   - Parallel analysis when possible

### Current Agents

1. **OS Agent** - SUSE Linux Specialist
   - Kernel and system-level changes
   - Package management (zypper, RPM)
   - cgroups v1/v2, systemd, drivers
   - Container runtime compatibility

2. **Kubernetes Agent** - Container Orchestration
   - Kubelet, kube-proxy, API server
   - Container runtimes (containerd, CRI-O)
   - CNI networking plugins
   - CSI storage drivers
   - Pod QoS and resource management

3. **Database Agent** - Example Extension
   - Shows how to add new agents
   - Analyzes database impacts
   - Extensible pattern for any domain

## 🚀 Quick Start

### Simple Usage (Recommended)

```python
from core.models import Config
from core.orchestrator import Orchestrator

# 1. Setup
config = Config()
orchestrator = Orchestrator(config)

# 2. Analyze - just provide two OS versions!
analysis = orchestrator.analyze_simple(
    from_version="SLES 15 SP6",
    to_version="SLES 15 SP7"
)

# 3. Use results
print(f"OS Changes: {len(analysis['os_analysis']['changes'])}")
print(f"K8s Impacts: {len(analysis['downstream_impacts']['kubernetes-agent']['impacts'])}")
```

That's it! The system automatically cascades through all agents.

## 📦 Installation

```bash
cd os_k8s_agent_system
pip install -r requirements.txt

# Setup API key
cp .env.template .env
# Edit .env with your API key (both primary and backup Google API key)

# Run
python main.py
```

## 📚 Internal Document Management

The system can combine **online scraped data** with **internal company documents** (PDFs, policies, configs) for comprehensive analysis.

### Adding Internal Documents

Use the `manage_docs.py` CLI to add your company's internal documents:

```bash
# Add a Kubernetes policy document
python manage_docs.py add docs/k8s-policy.pdf --category kubernetes --tags policy,versions

# Add an OS hardening guide
python manage_docs.py add docs/sles-hardening.pdf --category os --description "SLES security guide"

# Add a general document
python manage_docs.py add docs/upgrade-procedures.md --category general
```

### Document Categories

| Category | Used By | Description |
|----------|---------|-------------|
| `kubernetes` | Kubernetes Agent | K8s version policies, container runtime requirements |
| `os` | OS Agent | OS hardening guides, kernel configurations |
| `general` | All Agents | General upgrade procedures, policies |

### Managing Documents

```bash
# List all documents
python manage_docs.py list

# List only kubernetes documents
python manage_docs.py list --category kubernetes

# Search documents
python manage_docs.py search "container runtime version"

# View stats
python manage_docs.py stats

# Remove a document
python manage_docs.py remove doc_20260206_120000_policy
```

### How It Works

When you run an analysis, the system:
1. **Scrapes online sources** (SUSE release notes, Kubernetes docs)
2. **Searches internal documents** for relevant context
3. **Combines both sources** with LLM analysis
4. **Cites sources** in the final report

Example workflow:
```bash
# 1. Add your company's K8s policy
python manage_docs.py add company_k8s_policy.pdf --category kubernetes

# 2. Run analysis - internal docs are automatically used
python main.py --from "SLES 15 SP6" --to "SLES 15 SP7"

# 3. Check the report - it will reference both online and internal sources
```

## 🚀 Quick Start - End-to-End Usage

### 1. Configure API Keys

Edit the `.env` file with your API keys:
```bash
# Primary API key (OpenRouter)
OPENAI_API_KEY=your-openrouter-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Backup API key (Google AI - will be used if primary exhausts)
GOOGLE_API_KEY=your-google-api-key-here

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=openai/gpt-4o-mini
```

### 2. Run the System

```bash
python main.py
```

### 3. Provide OS Versions

When prompted, enter your OS versions:
```
Enter current OS version (e.g., SLES 15 SP6): SLES 15 SP6
Enter new OS version (e.g., SLES 15 SP7): SLES 15 SP7
```

The system will automatically:
- Analyze OS-level changes between the versions
- Identify Kubernetes impacts
- Provide mitigation steps
- Generate detailed reports (JSON, Markdown, Console)
- Use backup API key if primary exhausts

### 4. View Results

Reports are generated in the current directory:
- `analysis_report_YYYYMMDD_HHMMSS.json` - Machine-readable JSON
- `analysis_report_YYYYMMDD_HHMMSS.md` - Human-readable Markdown
- Console output with color-coded tables

## 🎓 Examples

See `examples.py` for comprehensive usage patterns. Run with:
```bash
python examples.py
```

## 📚 Knowledge Base (Optional)
```python
knowledge_sources = {
    "directories": [
        "./company_docs/",
        "./kubernetes_configs/"
    ]
}
```

## 📖 Usage

### Basic Usage

```bash
python main.py
```

### Programmatic Usage

```python
from core.models import Config, VersionChange
from core.orchestrator import Orchestrator

# Initialize
config = Config()
orchestrator = Orchestrator(config)

# Load knowledge
orchestrator.load_knowledge_base({
    "pdfs": ["./docs/k8s-guide.pdf"],
    "web_pages": ["https://docs.suse.com/..."]
})

# Analyze version change
version_change = VersionChange(
    layer="OS",
    from_version="SLES 15 SP6",
    to_version="SLES 15 SP7",
    workload="Kubernetes"
)

analysis = orchestrator.analyze_version_change(version_change)

# Generate reports
orchestrator.generate_report(
    analysis,
    output_formats=["console", "json", "markdown"]
)
```

## 📊 Output Formats

### 1. Console (Rich Tables)
Beautiful color-coded tables with:
- Breaking changes by severity
- Kubernetes impact analysis
- Mitigation steps with priorities
- Evidence-based recommendations

### 2. JSON (Machine-Readable)
Structured data for automation:
```json
{
  "upgrade": {...},
  "breaking_changes": [...],
  "kubernetes_impact": [...],
  "mitigation_steps": [...],
  "recommendations": [...]
}
```

### 3. Markdown (Documentation)
Human-readable reports with:
- Executive summary
- Detailed tables
- Actionable steps

## 🎨 Example Output

```
================================================================================
   OS & KUBERNETES VERSION IMPACT ANALYSIS
================================================================================

📊 Upgrade Analysis:
   From: SLES 15 SP6
   To:   SLES 15 SP7
   Workload: Kubernetes

🤖 Analysis Metadata:
   Confidence: 95%
   Evidence Sources: 12

🔥 BREAKING CHANGES (5)

┌────────────┬─────────────────────┬──────────┬─────────────────┬──────────┐
│ Severity   │ Component           │ Type     │ Description     │ K8s Impact│
├────────────┼─────────────────────┼──────────┼─────────────────┼──────────┤
│ 🔴 CRITICAL│ Container Registry  │ breaking │ Default Docker  │ kubelet, │
│            │ Configuration       │          │ Hub removed...  │ runtime  │
└────────────┴─────────────────────┴──────────┴─────────────────┴──────────┘

☸️  KUBERNETES IMPACT (3)
...
```

## 🔧 Extending the System

### Add New Agents

```python
# agents/runtime_agent.py
class RuntimeAgent:
    """Container runtime specialist"""
    
    def analyze_runtime_compatibility(self, os_changes):
        # Analyze CRI-O, containerd compatibility
        ...
```

### Add New Knowledge Sources

```python
# Add database support
def ingest_database(self, query):
    """Ingest from internal database"""
    ...
```

### Customize Reports

```python
# core/report_generator.py
def generate_html_report(self, analysis):
    """Generate interactive HTML dashboard"""
    ...
```

## 📝 Knowledge Base Management

### View Knowledge Stats
```python
stats = orchestrator.kb.search("cgroups v2", k=5)
print(f"Found {len(stats)} relevant documents")
```

### Update Knowledge
```python
# Add new documentation
orchestrator.kb.ingest_pdf("./docs/new-release-notes.pdf")
```

### Search Knowledge
```python
context = orchestrator.kb.get_relevant_context(
    "kernel changes affecting kubelet",
    max_tokens=4000
)
```

## 🔒 Security

- API keys stored in `.env` (excluded from git)
- Knowledge base stored locally
- No data sent to external services except LLM API

## 🤝 Contributing

This is designed to be extended:
1. Add specialized agents for other layers (networking, storage, security)
2. Integrate with CI/CD pipelines
3. Add webhooks for automatic analysis
4. Create web UI dashboard

## 📚 Resources

- SUSE Documentation: https://www.suse.com/documentation/
- Kubernetes Docs: https://kubernetes.io/docs/
- LangChain: https://python.langchain.com/

## ❓ FAQ

**Q: Which LLM should I use?**
A: GPT-4 Turbo recommended for best analysis quality. Claude 3 Opus is also excellent.

**Q: How much does it cost?**
A: Depends on knowledge base size. Typical analysis: $0.10-0.50 per run.

**Q: Can I use it offline?**
A: Not fully - requires LLM API. You can use local LLMs (Ollama) with modifications.

**Q: How accurate is the analysis?**
A: Depends on knowledge base quality. With good documentation, 90-95% confidence.

---

**Need API Keys?**
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
