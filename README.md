# Analysis Agent - OS & Kubernetes Version Impact Analysis

Multi-agent AI system for analyzing OS version upgrades and their impact on Kubernetes workloads.

## 🎯 Overview

This project provides two complementary approaches to analyzing SUSE Linux Enterprise Server (SLES) version upgrades:

1. **suse_compatibility_agent**: Integration with mino.ai API for rapid analysis
2. **os_k8s_agent_system**: Full-featured multi-agent system with LangChain, RAG, and custom agents

## 📁 Project Structure

```
.
├── suse_compatibility_agent/     # mino.ai API integration
│   ├── suse_k8s_analyzer.py      # SSE streaming analysis
│   └── suse15_sp6_to_sp7_analysis.json  # Sample analysis output
│
└── os_k8s_agent_system/          # Multi-agent analysis system
    ├── agents/                   # Specialized AI agents
    │   ├── os_agent.py          # SUSE OS specialist
    │   └── kubernetes_agent.py  # K8s impact analyzer
    ├── core/                    # Core system components
    │   ├── models.py           # Data models
    │   ├── knowledge_base.py   # RAG system
    │   ├── orchestrator.py     # Agent coordinator
    │   └── report_generator.py # Report formatting
    ├── main.py                 # Main entry point
    └── .env.template          # Configuration template
```

## 🚀 Quick Start

### System 1: mino.ai Integration

```bash
cd suse_compatibility_agent
pip install requests python-dotenv
python suse_k8s_analyzer.py
```

### System 2: Multi-Agent Analysis

```bash
cd os_k8s_agent_system

# Install uv package manager (Windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create virtual environment
uv venv

# Install dependencies
uv pip install langchain langchain-openai langchain-text-splitters langchain-community chromadb PyPDF2 pymupdf beautifulsoup4 requests pandas tabulate rich python-dotenv

# Configure API key
copy .env.template .env
# Edit .env and add your OpenAI/OpenRouter API key

# Run analysis
python main.py
```

## 🔧 Configuration

Create `.env` file in `os_k8s_agent_system/`:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Or OpenRouter Configuration
OPENAI_API_KEY=your-openrouter-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
```

## 📊 Output Formats

The system generates comprehensive reports in multiple formats:

- **Console**: Beautiful formatted tables with color coding
- **JSON**: Structured data for programmatic use
- **Markdown**: Detailed documentation with sections for:
  - Executive summary
  - Breaking changes analysis
  - Kubernetes impact assessment
  - Mitigation steps (pre/during/post upgrade)
  - Strategic recommendations

## 🎯 Use Cases

- **OS Upgrade Planning**: Identify breaking changes between SUSE versions
- **Kubernetes Compatibility**: Assess impact on K8s workloads
- **Risk Assessment**: Evaluate severity of changes (CRITICAL/HIGH/MEDIUM/LOW)
- **Migration Planning**: Generate actionable mitigation steps
- **Documentation**: Create comprehensive upgrade documentation

## 📖 Key Features

### OS Agent
- SUSE Linux specialist with deep OS knowledge
- Analyzes kernel changes, driver updates, package removals
- Identifies cgroups v1/v2 transitions
- Detects container runtime configuration changes

### Kubernetes Agent
- K8s expert analyzing workload impacts
- Maps OS changes to kubelet, CRI, CNI, CSI impacts
- Identifies Pod QoS and resource management issues
- Provides specific configuration remediation

### Knowledge Base (RAG)
- Ingests PDFs, text files, web pages
- Vector embeddings for semantic search
- Provides context-aware analysis
- Supports custom company documentation

## 🛠️ Technologies

- **LangChain**: Agent orchestration and LLM integration
- **ChromaDB**: Vector database for RAG
- **OpenAI/OpenRouter**: LLM providers
- **Rich**: Beautiful console output
- **Pydantic**: Data validation and modeling

## 📝 Example Analysis

```json
{
  "upgrade": {
    "from_version": "SLES 15 SP6",
    "to_version": "SLES 15 SP7",
    "workload": "Kubernetes"
  },
  "breaking_changes": [
    {
      "component": "Container Runtime Configuration",
      "impact_severity": "CRITICAL",
      "description": "Default container registry entries removed...",
      "affected_k8s_components": ["kubelet", "container runtime"]
    }
  ],
  "kubernetes_impact": [...],
  "mitigation_steps": [...],
  "recommendations": [...]
}
```

## 🤝 Contributing

This is an educational/enterprise project for OS upgrade impact analysis.

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Links

- GitHub: https://github.com/adityashravan/Analysis_agent-
- SUSE Documentation: https://www.suse.com/releasenotes/

---

**Note**: This system requires API keys for OpenAI or OpenRouter. The analysis quality depends on the LLM model used and the knowledge base provided.
