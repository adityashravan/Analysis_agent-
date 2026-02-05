"""
OS Agent - SUSE Specialist (Mino-Inspired Architecture)
Analyzes OS version changes and their impacts using efficient LLM calls
"""

import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from core.models import (
    VersionChange, BreakingChange, MitigationStep,
    ImpactAnalysis, AgentMetadata, AnalysisReport
)
from core.knowledge_base import KnowledgeBaseManager

logger = logging.getLogger(__name__)


class OSAgent:
    """
    Senior Linux OS Compatibility Engineer (SUSE)
    
    Mino-Inspired Optimizations:
    - Hierarchical prompting (reduce expensive LLM calls)
    - Response caching (avoid duplicate calls)
    - Goal-based extraction (structured output)
    - Streaming support for progress feedback
    
    Specializes in:
    - SUSE Linux Enterprise Server internals
    - Kernel and system-level changes
    - OS-level dependency management
    """
    
    # Response cache (Mino-style cost reduction)
    _cache: Dict[str, Any] = {}
    _cache_dir = Path("./cache")
    
    def __init__(self, config, knowledge_base: KnowledgeBaseManager):
        self.config = config
        self.kb = knowledge_base
        
        # Ensure cache directory exists
        self._cache_dir.mkdir(exist_ok=True)
        
        # Initialize LLM with streaming for progress feedback (Mino SSE-style)
        callbacks = [StreamingStdOutCallbackHandler()] if config.use_streaming else []
        
        if config.llm_provider == "openai":
            llm_kwargs = {
                "model": config.llm_model,
                "temperature": 0.1,
                "openai_api_key": config.openai_api_key,
                "max_retries": config.max_retries,
            }
            if hasattr(config, 'openai_base_url') and config.openai_base_url:
                llm_kwargs["base_url"] = config.openai_base_url
            self.llm = ChatOpenAI(**llm_kwargs)
        else:
            self.llm = ChatAnthropic(
                model=config.llm_model,
                temperature=0.1,
                anthropic_api_key=config.anthropic_api_key
            )
        
        # Mino-Style Goal-Based Prompt (The "Secret Sauce")
        # This is the key to good results - structured task specification
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Linux OS Compatibility Engineer specializing in SUSE Linux Enterprise Server.

=== AGENT IDENTITY (Mino-Style) ===
Layer: Operating System
Responsibility: Detect OS-level changes and predict downstream Kubernetes impact
Output Consumer: Kubernetes Compatibility Agent

=== YOUR EXPERTISE ===
- SUSE Linux Enterprise Server internals and release notes
- Kernel version changes, driver updates, and system impacts
- System library and package management (zypper, RPM)
- cgroups v1/v2 transitions and container impacts
- Container runtime compatibility (CRI-O, containerd, podman)
- systemd, networking (DHCP, DNS), and init system changes

=== CONSTRAINTS ===
- Focus ONLY on OS-level changes
- Be EXTREMELY SPECIFIC - name exact packages, config files, drivers
- Cite specific sources and documentation URLs
- State impact severity honestly (CRITICAL/HIGH/MEDIUM/LOW)
- Do NOT propose Kubernetes architecture changes
- Do NOT include general release-note fluff"""),
            
            ("human", """=== TASK ===
Analyze the upgrade from {from_version} to {to_version} for Kubernetes workloads.

=== CONTEXT FROM KNOWLEDGE BASE ===
{context}

=== REQUIRED OUTPUT ===
Return a valid JSON object with this EXACT structure:

{{
  "breaking_changes": [
    {{
      "component": "Exact component name (e.g., 'Container Runtime Configuration', 'Kernel Driver Stability (smc)')",
      "change_type": "breaking|behavioral|deprecated",
      "description": "Detailed technical description. Include specific file paths, package names, configuration keys. Explain WHY this breaks existing functionality.",
      "impact_severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "affected_k8s_components": ["kubelet", "container runtime", "specific affected components"]
    }}
  ],
  "evidence_sources": [
    "https://www.suse.com/releasenotes/...",
    "Other documentation URLs"
  ],
  "mitigation_steps": [
    {{
      "step": "1",
      "action": "SPECIFIC action with exact commands, file paths, configuration changes. Example: 'Deploy configuration to pre-populate /etc/containers/registries.conf with explicit Docker Hub registry'",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "timing": "pre-upgrade|during-upgrade|post-upgrade"
    }}
  ],
  "recommendations": [
    "Specific strategic recommendations with business context"
  ]
}}

=== FOCUS AREAS ===
1. Removed or deprecated packages (like redis, dhcpd)
2. Kernel driver changes or known issues
3. Container registry configuration changes
4. System library version changes (glibc, systemd)
5. Networking stack changes (DHCP, DNS, time sync)
6. Security/authentication changes

=== OUTPUT RULES ===
- Name the EXACT component (package name, driver name, config file)
- Describe WHAT changed technically
- State WHY it breaks existing setups
- Specify affected K8s components
- Provide actionable mitigation with specific commands/paths
- Output ONLY the JSON object, no markdown, no explanations.""")
        ])
        
        self.impact_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are analyzing the downstream impact of OS changes on {target_layer}.
Map each OS-level change to specific impacts on the target layer."""),
            
            ("human", """OS Changes:
{os_changes}

Target Layer: {target_layer}
Context:
{context}

For each OS change, determine:
1. Which {target_layer} components are affected
2. How they are affected (specific behavior changes)
3. What actions are required to mitigate
4. Risk level of not taking action

Be specific about component names, configuration files, and required changes.""")
        ])
    
    def _get_cache_key(self, version_change: VersionChange) -> str:
        """Generate cache key for version change analysis"""
        key_str = f"{version_change.from_version}:{version_change.to_version}:{version_change.workload}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load cached analysis result (Mino-style cost reduction)"""
        if not self.config.enable_caching:
            return None
        
        cache_file = self._cache_dir / f"os_analysis_{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    logger.info(f"📦 Loading cached analysis: {cache_key[:8]}...")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Save analysis result to cache"""
        if not self.config.enable_caching:
            return
            
        cache_file = self._cache_dir / f"os_analysis_{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"💾 Cached analysis: {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def analyze_version_change(self, version_change: VersionChange) -> Dict[str, Any]:
        """
        Analyze OS version change (Mino-Inspired)
        
        Optimizations:
        - Check cache first (avoid duplicate LLM calls)
        - Single consolidated LLM call (not multiple small calls)
        - Structured JSON output
        """
        logger.info(f"OS Agent analyzing: {version_change.from_version} → {version_change.to_version}")
        
        # Check cache first (Mino 90% cost reduction principle)
        cache_key = self._get_cache_key(version_change)
        cached = self._load_from_cache(cache_key)
        if cached:
            logger.info("✅ Using cached analysis (saved LLM cost!)")
            return cached
        
        # Build search query
        print("   📡 Gathering context from knowledge base...", flush=True)
        query = f"""
        {version_change.from_version} {version_change.to_version} release notes
        breaking changes deprecated removed packages
        kernel changes driver issues systemd networking container runtime
        podman cri-o containerd registry configuration
        """
        
        # Get relevant context from knowledge base
        context = self.kb.get_relevant_context(query, max_tokens=8000)
        
        if not context or len(context.strip()) < 100:
            context = "No specific knowledge base context available. Use your knowledge of SUSE Enterprise Linux."
        
        # Run analysis with structured JSON output (Single LLM call - Mino efficiency)
        print("   🧠 Running LLM analysis (this is the main cost)...", flush=True)
        chain = self.analysis_prompt | self.llm
        result = chain.invoke({
            "from_version": version_change.from_version,
            "to_version": version_change.to_version,
            "context": context
        })
        
        # Parse JSON response
        import re
        
        content = result.content.strip()
        # Extract JSON if wrapped in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        try:
            analysis_data = json.loads(content)
            logger.info(f"OS Agent analysis complete: {len(analysis_data.get('breaking_changes', []))} breaking changes found")
            
            # Cache successful result
            self._save_to_cache(cache_key, analysis_data)
            
            return analysis_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {content[:500]}")
            # Return minimal structure
            return {
                "breaking_changes": [],
                "evidence_sources": [],
                "mitigation_steps": [],
                "recommendations": [],
                "parse_error": str(e),
                "raw_response": content
            }
    
    def analyze_impact(self, os_changes: str, target_layer: str) -> str:
        """
        Analyze impact of OS changes on target layer
        """
        query = f"{target_layer} compatibility {os_changes}"
        context = self.kb.get_relevant_context(query, max_tokens=4000)
        
        chain = self.impact_prompt | self.llm
        result = chain.invoke({
            "os_changes": os_changes,
            "target_layer": target_layer,
            "context": context
        })
        
        return result.content
    
    def get_metadata(self) -> AgentMetadata:
        """Get agent metadata"""
        return AgentMetadata(
            agent_name="suse-os-agent",
            domain="operating-system",
            confidence=0.0,  # Will be calculated based on evidence
            evidence_sources=[]
        )
