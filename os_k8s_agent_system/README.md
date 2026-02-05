# OS & Kubernetes Version Impact Analysis System

A multi-agent AI system for analyzing version changes and their cross-layer impacts, specifically designed for SUSE Linux and Kubernetes environments.

## 🎯 Purpose

This system answers critical questions like:
- **What changes between SUSE 15 SP6 and SUSE 15 SP7?**
- **If I upgrade to SUSE 15 SP7, what will break in Kubernetes?**
- **What are the required mitigation steps?**

## 🏗️ Architecture

### Multi-Agent System
```
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                            │
│              (Coordinates agent workflow)                    │
└────────┬─────────────────────────────────────┬──────────────┘
         │                                     │
    ┌────▼─────┐                        ┌─────▼────┐
    │ OS AGENT │                        │ K8S AGENT│
    │  (SUSE)  │                        │          │
    └────┬─────┘                        └─────┬────┘
         │                                     │
         └─────────┬───────────────────────────┘
                   │
          ┌────────▼─────────┐
          │ KNOWLEDGE BASE   │
          │  (RAG System)    │
          │ • PDFs           │
          │ • Docs           │
          │ • Web pages      │
          │ • Code repos     │
          └──────────────────┘
```

### Specialized Agents

1. **OS Agent** - SUSE Linux Specialist
   - Kernel and system-level changes
   - Package management
   - cgroups, systemd, drivers
   
2. **Kubernetes Agent** - K8s Compatibility Specialist
   - Kubelet and container runtime
   - CNI networking
   - Storage and CSI
   - QoS and resource management

3. **Knowledge Base** - RAG-powered context retrieval
   - Vector database (ChromaDB/FAISS)
   - Multi-source ingestion
   - Semantic search

## 🚀 Setup

### 1. Install Dependencies

```bash
cd os_k8s_agent_system
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy template
cp .env.template .env

# Edit .env and add your API key
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Add Your Knowledge Sources

The system can ingest:

#### PDFs (Company Documentation)
```python
knowledge_sources = {
    "pdfs": [
        "./docs/kubernetes-internal-docs.pdf",
        "./docs/suse-deployment-guide.pdf"
    ]
}
```

#### Text Files (Notes, Checklists)
```python
knowledge_sources = {
    "text_files": [
        "./knowledge/migration-notes.txt",
        "./knowledge/known-issues.md"
    ]
}
```

#### Web Pages (Official Documentation)
```python
knowledge_sources = {
    "web_pages": [
        "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP7/",
        "https://kubernetes.io/docs/setup/production-environment/"
    ]
}
```

#### Directories (Bulk Import)
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
