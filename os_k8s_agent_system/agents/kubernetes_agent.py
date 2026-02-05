"""
Kubernetes Agent
Analyzes Kubernetes compatibility and impacts
"""

import logging
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from core.models import AgentMetadata
from core.knowledge_base import KnowledgeBaseManager

logger = logging.getLogger(__name__)


class KubernetesAgent:
    """
    Kubernetes Compatibility Specialist
    Specializes in:
    - Kubernetes component dependencies
    - Container runtime (CRI-O, containerd) compatibility
    - kubelet configuration
    - CNI plugins and networking
    - Storage drivers and CSI
    """
    
    def __init__(self, config, knowledge_base: KnowledgeBaseManager):
        self.config = config
        self.kb = knowledge_base
        
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
            domain="container-orchestration",
            confidence=0.0,
            evidence_sources=[]
        )
