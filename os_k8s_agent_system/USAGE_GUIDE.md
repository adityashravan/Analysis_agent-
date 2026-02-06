# End-to-End Usage Guide

## Overview

This guide will walk you through using the OS & Kubernetes Version Impact Analysis System from start to finish.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- API keys:
  - **Primary**: OpenRouter API key (or OpenAI API key)
  - **Backup**: Google AI API key (optional but recommended)

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd os_k8s_agent_system
pip install -r requirements.txt
```

This will install all necessary packages including:
- `langchain-openai` - For LLM integration
- `langchain-anthropic` - Alternative LLM provider
- `chromadb` - Vector database for knowledge base
- `python-dotenv` - Environment variable management
- `rich` - Beautiful console output

### 2. Configure API Keys

Copy the template and edit with your keys:

```bash
cp .env.template .env
```

Edit `.env` file with your actual API keys:

```bash
# Primary API Key (OpenRouter - recommended for cost-effectiveness)
OPENAI_API_KEY=sk-or-v1-your-key-here
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# Backup API Key (Google AI - automatically used if primary exhausts)
GOOGLE_API_KEY=AIzaSy-your-google-api-key-here

# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=openai/gpt-4o-mini  # Cost-effective model

# Vector Store Configuration
VECTOR_STORE=chromadb
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Optimization Settings
ENABLE_CACHING=true
MAX_RETRIES=3
USE_STREAMING=false
```

**Get API Keys:**
- OpenRouter: https://openrouter.ai/ (provides access to multiple models)
- Google AI: https://makersuite.google.com/app/apikey
- OpenAI: https://platform.openai.com/api-keys (alternative)

### 3. Run the System

```bash
python main.py
```

### 4. Provide Input

When the system starts, you'll see:

```
====================================================================================================
  OS & KUBERNETES VERSION IMPACT ANALYSIS SYSTEM
  Multi-Agent Architecture with Upstream-Downstream Pattern
====================================================================================================

🔧 Step 1: Loading configuration...
✅ Configuration validated
   LLM Provider: openai
   Model: openai/gpt-4o-mini
   🔑 Backup API Keys: 1 available
   💡 Fallback: Enabled (will auto-switch if primary key exhausts)

🤖 Step 2: Initializing multi-agent system...
✅ Multi-agent system initialized
   Agents ready: OS Agent, Kubernetes Agent
   Dependency chain: OS Agent → Kubernetes Agent

📚 Step 3: Knowledge Base - Using LLM's built-in knowledge
----------------------------------------------------------------------------------------------------
   (To add custom sources, uncomment the knowledge_sources section below)

====================================================================================================
  USER INPUT
====================================================================================================

Please provide the OS version details:

Enter current OS version (e.g., SLES 15 SP6):
```

**Enter your OS versions:**

```
Enter current OS version (e.g., SLES 15 SP6): SLES 15 SP6
Enter new OS version (e.g., SLES 15 SP7): SLES 15 SP7
```

**Supported OS Formats:**
- SUSE Linux: `SLES 15 SP6`, `SLES 15 SP7`, etc.
- Ubuntu: `Ubuntu 20.04`, `Ubuntu 22.04`
- RHEL: `RHEL 8.5`, `RHEL 9.0`
- Any Linux distribution with version numbers

### 5. Analysis Process

The system will now:

1. **OS Agent Analysis** (20-30 seconds)
   - Analyzes OS-level changes between versions
   - Identifies kernel, library, and system changes
   - Detects breaking changes and deprecations

2. **Kubernetes Agent Analysis** (15-20 seconds)
   - Receives OS changes from OS Agent
   - Analyzes Kubernetes component impacts
   - Identifies required actions and migrations

3. **Report Generation** (5 seconds)
   - Console output with color-coded tables
   - JSON report for automation
   - Markdown report for documentation

### 6. View Results

#### Console Output

You'll see rich tables showing:

```
🔥 BREAKING CHANGES (5)
┌────────────┬─────────────────────┬──────────┬─────────────────┬──────────┐
│ Severity   │ Component           │ Type     │ Description     │ K8s Impact│
├────────────┼─────────────────────┼──────────┼─────────────────┼──────────┤
│ 🔴 CRITICAL│ Container Runtime   │ breaking │ cgroups v2...   │ kubelet  │
└────────────┴─────────────────────┴──────────┴─────────────────┴──────────┘

☸️  KUBERNETES IMPACT (3)
...

🛠️  MITIGATION STEPS (7)
...
```

#### JSON Report

Location: `./analysis_report_YYYYMMDD_HHMMSS.json`

```json
{
  "upgrade": {
    "from_version": "SLES 15 SP6",
    "to_version": "SLES 15 SP7",
    "workload": "Kubernetes"
  },
  "os_analysis": {
    "changes": [
      {
        "component": "Container Runtime",
        "change_type": "breaking",
        ...
      }
    ],
    "mitigation_steps": [...],
    "recommendations": [...]
  },
  "downstream_impacts": {
    "kubernetes-agent": {
      "impacts": [...],
      "required_actions": [...],
      "risk_level": "HIGH"
    }
  }
}
```

#### Markdown Report

Location: `./analysis_report_YYYYMMDD_HHMMSS.md`

Human-readable documentation with:
- Executive summary
- Detailed change tables
- Step-by-step mitigation guide
- Recommendations

## Automatic API Key Fallback

If your primary API key runs out of quota, the system will:

1. Detect the rate limit error
2. Display: `⚠️  Switched to fallback API key: sk-or-v1... -> AIzaSy...`
3. Retry the request with the backup key
4. Continue analysis without interruption

**No manual intervention required!**

## Customizing the Analysis

### Adding Knowledge Sources

Edit `main.py` to uncomment the knowledge sources section:

```python
# Load custom documentation
orchestrator.load_knowledge_base({
    "pdfs": ["./docs/k8s-deployment-guide.pdf"],
    "directories": ["./company_docs/"],
    "web_pages": ["https://docs.suse.com/..."]
})
```

### Changing the Model

Edit `.env`:

```bash
# Use more powerful model for better analysis
LLM_MODEL=openai/gpt-4-turbo

# Or use free models
LLM_MODEL=google/gemini-2.0-flash-exp:free
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution:**
- Check that `.env` file exists in `os_k8s_agent_system/` directory
- Ensure API key is properly set without quotes
- Run `python main.py` from the correct directory

### Issue: API rate limit errors

**Solution:**
- Add a backup API key to `.env`:
  ```bash
  GOOGLE_API_KEY=your-backup-key-here
  ```
- System will automatically switch to backup

### Issue: Analysis takes too long

**Solution:**
- Use a faster model:
  ```bash
  LLM_MODEL=openai/gpt-4o-mini
  ```
- Enable caching:
  ```bash
  ENABLE_CACHING=true
  ```

### Issue: Poor analysis quality

**Solution:**
- Use a more powerful model:
  ```bash
  LLM_MODEL=openai/gpt-4-turbo
  ```
- Add custom knowledge sources (see above)

## Advanced Usage

### Programmatic Usage

```python
from core.models import Config
from core.orchestrator import Orchestrator

# Initialize
config = Config()
orchestrator = Orchestrator(config)

# Analyze
analysis = orchestrator.analyze_simple(
    from_version="SLES 15 SP6",
    to_version="SLES 15 SP7"
)

# Access results
os_changes = analysis['os_analysis']['changes']
k8s_impacts = analysis['downstream_impacts']['kubernetes-agent']['impacts']

print(f"Found {len(os_changes)} OS changes")
print(f"Found {len(k8s_impacts)} Kubernetes impacts")
```

### Adding Custom Agents

See `ARCHITECTURE.md` for detailed guide on extending the system with new agents.

## Cost Estimation

Using `openai/gpt-4o-mini` on OpenRouter:
- Cost per analysis: ~$0.10 - $0.30
- Average tokens: 50,000 - 100,000
- Time: 30-60 seconds

Using free models (`google/gemini-2.0-flash-exp:free`):
- Cost: $0
- Quality: Good for basic analysis
- Time: 30-60 seconds

## Next Steps

1. **Run your first analysis** with the default SLES versions
2. **Review the generated reports** to understand the output format
3. **Try different OS versions** that match your use case
4. **Add custom knowledge sources** for better accuracy
5. **Extend with new agents** (database, network, etc.)

## Support

For issues or questions:
1. Check this guide first
2. Review `README.md` for architecture details
3. See `examples.py` for usage patterns
4. Check `ARCHITECTURE.md` for technical details

---

**Happy Analyzing! 🚀**
