"""
Kubernetes Agent
Analyzes Kubernetes compatibility and impacts from upstream changes

Enhanced with upstream-downstream pattern:
- Consumes OS-level changes from upstream OS Agent
- Identifies what breaks in Kubernetes when OS changes
- Can propagate to further downstream agents (e.g., application agents)
"""

import logging
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from core.models import AgentMetadata
from core.knowledge_base import KnowledgeBaseManager
from core.base_agent import BaseAgent, AgentChange
from core.document_store import get_document_store

logger = logging.getLogger(__name__)


class KubernetesAgent(BaseAgent):
    """
    Kubernetes Compatibility Specialist
    
    Specializes in:
    - Kubernetes component dependencies
    - Container runtime (CRI-O, containerd) compatibility
    - kubelet configuration
    - CNI plugins and networking
    - Storage drivers and CSI
    
    Upstream-Downstream Pattern:
    - Consumes changes from OS Agent
    - Analyzes impact on Kubernetes stack
    - Can propagate to application/workload agents
    
    Data Sources:
    - Online scraped documentation
    - Internal company documents (PDFs, policies)
    - LLM knowledge
    """
    
    def __init__(self, config, knowledge_base: KnowledgeBaseManager):
        # Initialize base agent
        super().__init__(config, knowledge_base, agent_name="kubernetes-agent", domain="container-orchestration")
        
        # Initialize document store for internal documents
        self.document_store = get_document_store()
        
        # Initialize LLM
        if config.llm_provider == "openai":
            llm_kwargs = {
                "model": config.llm_model,
                "temperature": 0.1,
                "openai_api_key": config.openai_api_key
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
        
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Kubernetes Compatibility Specialist.

Your expertise includes:
- Kubernetes components (kubelet, kube-proxy, API server)
- Container Runtime Interface (CRI) - CRI-O, containerd
- Container Networking Interface (CNI)
- Storage (CSI drivers, volume plugins)
- Pod QoS and resource management
- Kubernetes version compatibility

Your responsibility:
- Analyze OS changes for Kubernetes impact
- Identify compatibility issues
- Recommend configuration changes
- Provide migration paths"""),
            
            ("human", """OS Changes detected:
{os_changes}

Kubernetes Context:
{context}

Task:
1. For each OS change, determine Kubernetes impact:
   - Affected Kubernetes components
   - Behavior changes in K8s
   - Configuration changes required
   - Risk of not addressing

2. Focus on:
   - kubelet and container runtime integration
   - Cgroups driver configuration
   - Pod networking and CNI
   - Storage and volume management
   - QoS and resource limits
   - Security and RBAC

3. Provide specific actions:
   - Configuration file changes
   - Version upgrade requirements
   - Testing procedures

Be specific about file paths, configuration parameters, and Kubernetes versions.""")
        ])
    
    def analyze_os_impact(self, os_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze how OS changes impact Kubernetes
        Returns structured JSON with kubernetes_impact details
        """
        logger.info("Kubernetes Agent analyzing OS impacts...")
        
        # Extract breaking changes from OS analysis
        breaking_changes = os_analysis.get("breaking_changes", [])
        if not breaking_changes:
            logger.warning("No breaking changes to analyze")
            return {"kubernetes_impact": []}
        
        # Build context query
        components = []
        for change in breaking_changes:
            components.extend(change.get("affected_k8s_components", []))
        query = f"Kubernetes {' '.join(set(components))} container runtime kubelet impacts"
        context = self.kb.get_relevant_context(query, max_tokens=4000)
        
        # Format OS changes as readable text for the prompt
        os_changes_text = "\n".join([
            f"- {c['component']}: {c['description']}" 
            for c in breaking_changes
        ])
        
        # Update prompt to request JSON output
        from langchain_core.prompts import ChatPromptTemplate
        json_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Kubernetes expert analyzing OS-level changes.
            
Output a JSON object with this structure:
{{
  "kubernetes_impact": [
    {{
      "k8s_component": "specific K8s component name",
      "impact_description": "detailed description of how the OS change affects this component",
      "required_actions": ["specific action 1", "specific action 2"]
    }}
  ]
}}
            
Be specific about component names, configuration files, and required actions.
Output ONLY the JSON object."""),
            ("human", """OS Changes:
{os_changes}

Context: {context}

Analyze Kubernetes impacts and output JSON only.""")
        ])
        
        chain = json_prompt | self.llm
        result = chain.invoke({
            "os_changes": os_changes_text,
            "context": context if context else "Use your Kubernetes knowledge."
        })
        
        # Parse JSON
        import json
        import re
        content = result.content.strip()
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        try:
            k8s_data = json.loads(content)
            logger.info(f"Kubernetes Agent analysis complete: {len(k8s_data.get('kubernetes_impact', []))} impacts found")
            return k8s_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse K8s JSON: {e}")
            return {
                "kubernetes_impact": [],
                "parse_error": str(e),
                "raw_response": content
            }
    
    def get_metadata(self) -> AgentMetadata:
        """Get agent metadata"""
        return AgentMetadata(
            agent_name="kubernetes-agent",
            domain="kubernetes",
            confidence=0.0,
            evidence_sources=[]
        )
    
    # BaseAgent abstract methods implementation
    
    def analyze_changes(self, **kwargs) -> Dict[str, Any]:
        """
        Direct analysis of Kubernetes changes (less common - usually triggered by upstream)
        
        This would be used if user wants to analyze Kubernetes version upgrade directly
        """
        logger.info("Kubernetes Agent: Direct analysis mode")
        
        # Could implement Kubernetes version upgrade analysis here
        # For now, this is a placeholder
        return {
            'changes': [],
            'metadata': self.get_metadata(),
            'note': 'Kubernetes Agent typically analyzes upstream OS changes. Use analyze_upstream_impact().'
        }
    
    def analyze_upstream_impact(self, upstream_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze how OS changes impact Kubernetes
        
        This is the main method - called when OS Agent propagates changes
        
        Data Sources Combined:
        1. Upstream OS changes from OS Agent
        2. Internal company documents (PDFs, policies)
        3. Knowledge base context
        4. LLM knowledge
        
        Args:
            upstream_changes: List of OS-level changes from OS Agent
            
        Returns:
            Kubernetes impact analysis with specific component impacts
        """
        logger.info(f"Kubernetes Agent: Analyzing impact of {len(upstream_changes)} OS changes...")
        
        if not upstream_changes:
            return {
                'impacts': [],
                'required_actions': [],
                'risk_level': 'LOW'
            }
        
        # Build context from upstream changes
        os_changes_summary = self._format_upstream_changes(upstream_changes)
        
        # Get relevant K8s context from knowledge base
        components = set()
        for change in upstream_changes:
            affected = change.get('metadata', {}).get('affected_k8s_components', [])
            components.update(affected)
        
        query = f"Kubernetes {' '.join(components)} container runtime kubelet impacts"
        context = self.kb.get_relevant_context(query, max_tokens=4000)
        
        # === NEW: Get internal document context ===
        internal_doc_query = f"Kubernetes version compatibility {' '.join(components)} container runtime policy"
        internal_context = self.document_store.get_context_for_agent(
            agent_type="kubernetes",
            query=internal_doc_query,
            max_chars=6000
        )
        
        internal_doc_text = ""
        internal_sources = []
        if internal_context.get("context"):
            internal_doc_text = internal_context["context"]
            internal_sources = internal_context.get("sources", [])
            logger.info(f"Kubernetes Agent: Found {internal_context['chunks_used']} relevant internal document sections")
            print(f"\n📚 INTERNAL DOCUMENTS: {internal_context['chunks_used']} sections from {len(internal_sources)} documents")
            for src in internal_sources[:5]:
                print(f"   📄 {src}")
        else:
            logger.info("Kubernetes Agent: No internal documents found")
            print("\n📚 INTERNAL DOCUMENTS: None loaded (use manage_docs.py to add)")
        
        # Analyze impacts using LLM
        impact_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Kubernetes expert analyzing OS-level changes.

Your expertise:
- Kubernetes internals (kubelet, kube-proxy, API server, controller manager)
- Container runtimes (containerd, CRI-O, Docker)
- Cgroups v1/v2 transition impacts
- CNI networking and network plugins
- CSI storage and volume management
- Pod QoS, resource limits, and scheduling

You have access to THREE data sources:
1. OS CHANGES: Changes from OS Agent (official release notes)
2. INTERNAL DOCUMENTS: Company-specific policies, version requirements, configurations
3. KNOWLEDGE BASE: General Kubernetes documentation

Your responsibility:
- Identify EXACTLY what breaks in Kubernetes when OS changes
- Cross-reference with internal company policies and version constraints
- Specify configuration files and parameters that need updates
- Assess risk levels honestly
- Provide actionable mitigation steps
- Note any conflicts with internal company policies

Output a JSON object with this structure:
{{
  "impacts": [
    {{
      "k8s_component": "specific component (e.g., 'kubelet', 'containerd', 'calico CNI')",
      "impact_description": "detailed description of what breaks and why",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "affected_features": ["specific K8s features affected"],
      "symptoms": ["what users will observe if not fixed"],
      "required_actions": ["specific config changes with file paths"],
      "config_files": ["/path/to/config.yaml"],
      "testing_steps": ["how to verify the fix"],
      "source_reference": "which source this came from (internal doc, KB, or OS change)"
    }}
  ],
  "risk_assessment": {{
    "overall_risk": "CRITICAL|HIGH|MEDIUM|LOW",
    "critical_components": ["components that must be addressed"],
    "optional_components": ["components that are nice to fix"]
  }},
  "internal_policy_conflicts": ["any conflicts with internal company documents"],
  "version_compatibility": {{
    "current_k8s_version": "from internal docs if found",
    "recommended_k8s_version": "based on new OS",
    "upgrade_required": true/false
  }},
  "migration_timeline": {{
    "pre_upgrade": ["actions before OS upgrade"],
    "during_upgrade": ["actions during upgrade"],
    "post_upgrade": ["actions after upgrade"],
    "validation": ["how to validate K8s still works"]
  }}
}}

Be specific about:
- Exact configuration file paths (e.g., /etc/kubernetes/kubelet.conf)
- Specific parameters to change
- Kubernetes version requirements
- Container runtime version requirements
- References to internal documents when applicable"""),
            ("human", """OS Changes Detected:
{os_changes}

=== INTERNAL COMPANY DOCUMENTS ===
{internal_docs}

=== KNOWLEDGE BASE CONTEXT ===
{context}

Analyze Kubernetes impacts considering ALL sources above. Output JSON only.""")
        ])
        
        chain = impact_prompt | self.llm
        result = chain.invoke({
            "os_changes": os_changes_summary,
            "internal_docs": internal_doc_text if internal_doc_text else "No internal documents loaded. Use manage_docs.py to add company policies.",
            "context": context if context else "Use your Kubernetes knowledge."
        })
        
        # Parse JSON response
        import json
        import re
        content = result.content.strip()
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        try:
            k8s_analysis = json.loads(content)
            impacts = k8s_analysis.get('impacts', [])
            
            logger.info(f"Kubernetes Agent: Found {len(impacts)} component impacts")
            
            # Convert to standardized format
            result = {
                'impacts': impacts,
                'required_actions': self._extract_actions(impacts),
                'risk_level': k8s_analysis.get('risk_assessment', {}).get('overall_risk', 'MEDIUM'),
                'internal_policy_conflicts': k8s_analysis.get('internal_policy_conflicts', []),
                'version_compatibility': k8s_analysis.get('version_compatibility', {}),
                'migration_timeline': k8s_analysis.get('migration_timeline', {}),
                'metadata': {
                    'agent_name': self.agent_name,
                    'domain': self.domain,
                    'upstream_changes_analyzed': len(upstream_changes),
                    'internal_docs_used': len(internal_sources),
                    'internal_doc_sources': internal_sources
                }
            }
            
            # If this K8s agent has downstream agents (e.g., app agents), propagate
            if self._downstream_agents and impacts:
                logger.info("Kubernetes Agent: Propagating to downstream agents...")
                downstream_results = self.propagate_to_downstream(impacts)
                result['downstream_impacts'] = downstream_results
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Kubernetes Agent: JSON parse error: {e}")
            return {
                'impacts': [],
                'required_actions': [],
                'risk_level': 'UNKNOWN',
                'error': str(e),
                'raw_response': content[:500]
            }
    
    def _format_upstream_changes(self, changes: List[Dict[str, Any]]) -> str:
        """Format upstream changes for LLM prompt"""
        lines = []
        for i, change in enumerate(changes, 1):
            lines.append(f"{i}. {change.get('component', 'Unknown Component')}")
            lines.append(f"   Type: {change.get('change_type', 'unknown')}")
            lines.append(f"   Severity: {change.get('severity', 'MEDIUM')}")
            lines.append(f"   Description: {change.get('description', 'No description')}")
            lines.append("")
        return "\n".join(lines)
    
    def _extract_actions(self, impacts: List[Dict[str, Any]]) -> List[str]:
        """Extract all required actions from impacts"""
        actions = []
        for impact in impacts:
            actions.extend(impact.get('required_actions', []))
        return actions
