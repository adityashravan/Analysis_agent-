"""
Database Agent - Example Downstream Agent
Analyzes how OS changes impact database workloads

This is an EXAMPLE showing how to add new agents to the system.
Demonstrates the extensibility of the upstream-downstream pattern.
"""

import logging
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from core.knowledge_base import KnowledgeBaseManager
from core.base_agent import BaseAgent, AgentChange

logger = logging.getLogger(__name__)


class DatabaseAgent(BaseAgent):
    """
    Database Compatibility Specialist
    
    Specializes in:
    - PostgreSQL, MySQL, MongoDB impacts
    - Database driver compatibility
    - Connection pooling and networking
    - Storage and I/O impacts
    - Performance implications
    
    Upstream Dependencies:
    - OS Agent (for system library changes)
    - Kubernetes Agent (for pod/container impacts)
    """
    
    def __init__(self, config, knowledge_base: KnowledgeBaseManager):
        super().__init__(config, knowledge_base, agent_name="database-agent", domain="database")
        
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
    
    def analyze_changes(self, **kwargs) -> Dict[str, Any]:
        """
        Direct database analysis (e.g., database version upgrade)
        """
        logger.info("Database Agent: Direct analysis mode")
        
        # Could implement database version upgrade analysis
        return {
            'changes': [],
            'metadata': self.get_metadata(),
            'note': 'Database Agent typically analyzes upstream changes from OS/K8s agents'
        }
    
    def analyze_upstream_impact(self, upstream_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze how OS/K8s changes impact databases
        
        Args:
            upstream_changes: OS or Kubernetes changes
            
        Returns:
            Database impact analysis
        """
        logger.info(f"Database Agent: Analyzing {len(upstream_changes)} upstream changes...")
        
        if not upstream_changes:
            return {
                'impacts': [],
                'required_actions': [],
                'risk_level': 'LOW'
            }
        
        # Format changes for analysis
        changes_summary = self._format_changes(upstream_changes)
        
        # Get database-relevant context
        query = "database PostgreSQL MySQL MongoDB driver compatibility storage performance"
        context = self.kb.get_relevant_context(query, max_tokens=4000)
        
        # Analyze using LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Database Compatibility Expert.

Your expertise:
- PostgreSQL, MySQL, MongoDB, Redis on Linux
- Database drivers and client libraries
- Connection pooling (pgpool, ProxySQL)
- Storage and I/O subsystems
- Network protocol changes
- Performance tuning and configuration

Your task:
Analyze how OS/Kubernetes changes impact database workloads.

Output JSON with this structure:
{{
  "impacts": [
    {{
      "database_type": "PostgreSQL|MySQL|MongoDB|Redis|Generic",
      "impact_description": "what breaks and why",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "affected_features": ["specific features"],
      "required_actions": ["specific fixes"],
      "config_files": ["/path/to/config"],
      "testing_steps": ["validation steps"]
    }}
  ],
  "risk_assessment": {{
    "overall_risk": "CRITICAL|HIGH|MEDIUM|LOW",
    "data_safety": "assessment of data loss risk",
    "downtime_required": "yes|no|maybe"
  }}
}}"""),
            ("human", """Upstream Changes:
{changes}

Database Context:
{context}

Analyze database impacts and output JSON only.""")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({
            "changes": changes_summary,
            "context": context if context else "Use your database knowledge."
        })
        
        # Parse JSON
        import json
        import re
        content = result.content.strip()
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        try:
            db_analysis = json.loads(content)
            impacts = db_analysis.get('impacts', [])
            
            logger.info(f"Database Agent: Found {len(impacts)} database impacts")
            
            return {
                'impacts': impacts,
                'required_actions': self._extract_actions(impacts),
                'risk_level': db_analysis.get('risk_assessment', {}).get('overall_risk', 'MEDIUM'),
                'risk_assessment': db_analysis.get('risk_assessment', {}),
                'metadata': {
                    'agent_name': self.agent_name,
                    'domain': self.domain,
                    'upstream_changes_analyzed': len(upstream_changes)
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Database Agent: JSON parse error: {e}")
            return {
                'impacts': [],
                'required_actions': [],
                'risk_level': 'UNKNOWN',
                'error': str(e)
            }
    
    def _format_changes(self, changes: List[Dict[str, Any]]) -> str:
        """Format changes for LLM prompt"""
        lines = []
        for i, change in enumerate(changes, 1):
            lines.append(f"{i}. {change.get('component', 'Unknown')}")
            lines.append(f"   {change.get('description', '')}")
            lines.append("")
        return "\n".join(lines)
    
    def _extract_actions(self, impacts: List[Dict[str, Any]]) -> List[str]:
        """Extract all required actions"""
        actions = []
        for impact in impacts:
            actions.extend(impact.get('required_actions', []))
        return actions
