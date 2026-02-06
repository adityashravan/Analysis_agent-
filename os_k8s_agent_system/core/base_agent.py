"""
Base Agent Interface for Scalable Multi-Agent Architecture

Implements upstream-downstream pattern where agents can:
1. Receive changes from upstream agents
2. Analyze impact on their domain
3. Propagate changes to downstream agents
4. Register new downstream agents dynamically
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class AgentChange(Dict):
    """
    Standard format for changes propagated between agents
    Contains: component, change_type, description, severity, metadata
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setdefault('component', 'unknown')
        self.setdefault('change_type', 'unknown')
        self.setdefault('description', '')
        self.setdefault('severity', 'MEDIUM')
        self.setdefault('metadata', {})


class BaseAgent(ABC):
    """
    Base class for all agents in the system
    
    Key Concepts:
    - Each agent specializes in one domain (OS, Kubernetes, Database, etc.)
    - Agents can have downstream dependencies (subscribers)
    - Changes flow: Upstream Agent -> This Agent -> Downstream Agents
    - Agents analyze impact and propagate relevant changes
    """
    
    def __init__(self, config, knowledge_base, agent_name: str, domain: str):
        """
        Initialize base agent
        
        Args:
            config: System configuration
            knowledge_base: Knowledge base manager
            agent_name: Unique agent identifier
            domain: Domain this agent specializes in
        """
        self.config = config
        self.kb = knowledge_base
        self.agent_name = agent_name
        self.domain = domain
        
        # Downstream agents that depend on this agent's output
        self._downstream_agents: List['BaseAgent'] = []
        
        logger.info(f"Initialized {agent_name} (domain: {domain})")
    
    def register_downstream(self, agent: 'BaseAgent'):
        """
        Register a downstream agent that depends on this agent
        
        Example:
            os_agent.register_downstream(k8s_agent)
            os_agent.register_downstream(database_agent)
        """
        if agent not in self._downstream_agents:
            self._downstream_agents.append(agent)
            logger.info(f"{self.agent_name} -> {agent.agent_name} (downstream registered)")
    
    def get_downstream_agents(self) -> List['BaseAgent']:
        """Get list of registered downstream agents"""
        return self._downstream_agents
    
    @abstractmethod
    def analyze_changes(self, **kwargs) -> Dict[str, Any]:
        """
        Analyze changes in this agent's domain
        
        Returns:
            Dict containing:
            - changes: List[AgentChange] - changes detected in this domain
            - metadata: agent metadata (confidence, sources, etc.)
            - recommendations: high-level recommendations
        """
        pass
    
    @abstractmethod
    def analyze_upstream_impact(self, upstream_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze how upstream changes impact this agent's domain
        
        Args:
            upstream_changes: List of changes from upstream agent(s)
            
        Returns:
            Dict containing:
            - impacts: List of impacts on this domain
            - required_actions: Actions needed to handle upstream changes
            - risk_level: Overall risk assessment
        """
        pass
    
    def propagate_to_downstream(self, my_changes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Propagate changes to all downstream agents
        
        Args:
            my_changes: Changes detected by this agent
            
        Returns:
            Dict mapping agent_name -> analysis results
        """
        downstream_results = {}
        
        if not self._downstream_agents:
            logger.info(f"{self.agent_name}: No downstream agents to notify")
            return downstream_results
        
        logger.info(f"{self.agent_name}: Propagating {len(my_changes)} changes to {len(self._downstream_agents)} downstream agent(s)")
        
        for downstream_agent in self._downstream_agents:
            try:
                logger.info(f"  → Analyzing impact on {downstream_agent.agent_name}...")
                result = downstream_agent.analyze_upstream_impact(my_changes)
                downstream_results[downstream_agent.agent_name] = result
                
                # Continue cascade if downstream agent has its own dependencies
                downstream_changes = result.get('changes', [])
                if downstream_changes and downstream_agent.get_downstream_agents():
                    nested_results = downstream_agent.propagate_to_downstream(downstream_changes)
                    downstream_results[downstream_agent.agent_name]['downstream'] = nested_results
                    
            except Exception as e:
                logger.error(f"Failed to propagate to {downstream_agent.agent_name}: {e}")
                downstream_results[downstream_agent.agent_name] = {
                    "error": str(e),
                    "impacts": []
                }
        
        return downstream_results
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get agent metadata
        """
        return {
            "agent_name": self.agent_name,
            "domain": self.domain,
            "downstream_count": len(self._downstream_agents),
            "downstream_agents": [a.agent_name for a in self._downstream_agents]
        }


class AgentRegistry:
    """
    Central registry for all agents in the system
    Makes it easy to discover and wire up agent dependencies
    """
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent):
        """Register an agent"""
        self._agents[agent.agent_name] = agent
        logger.info(f"Registered agent: {agent.agent_name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name"""
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return list(self._agents.keys())
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Get agent dependency graph
        Returns: Dict mapping agent_name -> list of downstream agent names
        """
        graph = {}
        for name, agent in self._agents.items():
            graph[name] = [a.agent_name for a in agent.get_downstream_agents()]
        return graph
    
    def visualize_dependencies(self) -> str:
        """
        Create ASCII visualization of agent dependencies
        """
        graph = self.get_dependency_graph()
        lines = ["Agent Dependency Graph:", "=" * 50]
        
        for agent_name, downstream in graph.items():
            lines.append(f"\n{agent_name}")
            if downstream:
                for i, dep in enumerate(downstream):
                    prefix = "└──" if i == len(downstream) - 1 else "├──"
                    lines.append(f"  {prefix} {dep}")
            else:
                lines.append("  └── (no downstream dependencies)")
        
        return "\n".join(lines)
