# System Architecture Guide

## Overview

This system implements a **scalable upstream-downstream agent pattern** for analyzing technology stack changes and their cascading impacts.

## Core Concepts

### 1. Base Agent Interface

All agents extend `BaseAgent` which provides:
- Upstream-downstream relationship management
- Automatic change propagation
- Standardized interfaces

```python
class BaseAgent(ABC):
    @abstractmethod
    def analyze_changes(self, **kwargs) -> Dict[str, Any]:
        """Analyze changes in this agent's domain"""
        pass
    
    @abstractmethod
    def analyze_upstream_impact(self, upstream_changes: List[Dict]) -> Dict[str, Any]:
        """Analyze how upstream changes impact this domain"""
        pass
    
    def register_downstream(self, agent: 'BaseAgent'):
        """Register a dependent agent"""
        pass
    
    def propagate_to_downstream(self, changes: List[Dict]) -> Dict[str, Dict]:
        """Auto-propagate to all downstream agents"""
        pass
```

### 2. Agent Lifecycle

```
1. Initialization
   ↓
2. Registration (added to AgentRegistry)
   ↓
3. Dependency Wiring (register_downstream)
   ↓
4. Analysis Trigger
   ↓
5. Automatic Propagation (if has downstream agents)
   ↓
6. Results Aggregation
```

### 3. Change Flow

```
User Input (e.g., "SLES 15 SP6" → "SLES 15 SP7")
    ↓
OS Agent.analyze_changes()
    → Detects OS-level changes
    → Creates AgentChange objects
    ↓
OS Agent.propagate_to_downstream()
    → Automatically calls K8s Agent
    → Calls Database Agent (if registered)
    → Parallel execution where possible
    ↓
Each Downstream Agent.analyze_upstream_impact()
    → Receives upstream changes
    → Analyzes impact in their domain
    → Returns structured results
    ↓
Further propagation if downstream has dependencies
    ↓
Results aggregated into final report
```

## Agent Structure

### Root Agent (OS Agent)

**Responsibility**: Detect OS-level changes

**Key Methods**:
```python
def analyze_changes(from_version: str, to_version: str) -> Dict:
    # 1. Analyze OS changes using LLM
    # 2. Convert to AgentChange format
    # 3. Auto-propagate to downstream
    # 4. Return comprehensive results
```

**Downstream Agents**: Kubernetes, Database, Network, etc.

### Downstream Agent (Kubernetes Agent)

**Responsibility**: Analyze K8s impacts from OS changes

**Key Methods**:
```python
def analyze_upstream_impact(upstream_changes: List[Dict]) -> Dict:
    # 1. Receive OS changes
    # 2. Identify K8s components affected
    # 3. Determine required actions
    # 4. Return K8s-specific impacts
```

**Upstream Agent**: OS Agent
**Downstream Agents**: Application Agent, Monitoring Agent, etc.

## Data Flow

### Input Format
```python
{
    "from_version": "SLES 15 SP6",
    "to_version": "SLES 15 SP7"
}
```

### AgentChange Format
```python
{
    "component": "Container Runtime Configuration",
    "change_type": "breaking",
    "description": "Detail about what changed",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "metadata": {
        "affected_k8s_components": ["kubelet", "containerd"],
        "source": "os-agent"
    }
}
```

### Output Format
```python
{
    "upgrade": {
        "from_version": "...",
        "to_version": "..."
    },
    "os_analysis": {
        "changes": [AgentChange, ...],
        "mitigation_steps": [...],
        "recommendations": [...]
    },
    "downstream_impacts": {
        "kubernetes-agent": {
            "impacts": [...],
            "required_actions": [...],
            "risk_level": "HIGH"
        },
        "database-agent": {
            "impacts": [...],
            ...
        }
    },
    "agent_chain": {
        "os-agent": ["kubernetes-agent", "database-agent"],
        "kubernetes-agent": ["application-agent"]
    }
}
```

## Adding New Agents

### Step 1: Create Agent Class

```python
from core.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self, config, knowledge_base):
        super().__init__(
            config, 
            knowledge_base,
            agent_name="my-new-agent",
            domain="my-domain"
        )
        # Initialize your LLM, tools, etc.
    
    def analyze_changes(self, **kwargs):
        # Direct analysis in your domain
        # Called when this is the root agent
        return {
            'changes': [...],
            'metadata': {...}
        }
    
    def analyze_upstream_impact(self, upstream_changes):
        # Analyze how upstream changes affect your domain
        # Called when changes propagate from upstream
        
        # 1. Parse upstream changes
        # 2. Use LLM to analyze impacts
        # 3. Return structured results
        
        return {
            'impacts': [...],
            'required_actions': [...],
            'risk_level': 'MEDIUM'
        }
```

### Step 2: Register and Wire

```python
# In orchestrator or main
my_agent = MyNewAgent(config, kb)
orchestrator.add_agent(my_agent, upstream_agent_name="os-agent")

# Or directly
os_agent.register_downstream(my_agent)
```

### Step 3: Use It

```python
# That's it! Agent is now part of the cascade
analysis = orchestrator.analyze_simple("SLES 15 SP6", "SLES 15 SP7")

# Your agent's results are in downstream_impacts
my_results = analysis['downstream_impacts']['my-new-agent']
```

## Dependency Patterns

### Linear Chain
```
OS → Kubernetes → Application
```

```python
os_agent.register_downstream(k8s_agent)
k8s_agent.register_downstream(app_agent)
```

### Parallel Downstream
```
OS → Kubernetes
  → Database
  → Network
```

```python
os_agent.register_downstream(k8s_agent)
os_agent.register_downstream(db_agent)
os_agent.register_downstream(network_agent)
```

### Multi-Level Tree
```
OS → Kubernetes → App1
             → App2
  → Database → Cache
```

```python
os_agent.register_downstream(k8s_agent)
os_agent.register_downstream(db_agent)
k8s_agent.register_downstream(app1_agent)
k8s_agent.register_downstream(app2_agent)
db_agent.register_downstream(cache_agent)
```

## Best Practices

### 1. Agent Design
- **Single Responsibility**: Each agent focuses on one domain
- **Structured Output**: Always return JSON-parseable results
- **Error Handling**: Gracefully handle LLM failures
- **Logging**: Use logger for debugging

### 2. Prompt Engineering
- **Specific Instructions**: Tell LLM exactly what to analyze
- **Structured Output**: Request JSON format explicitly
- **Context Aware**: Use knowledge base for domain-specific info
- **Severity Levels**: Use consistent CRITICAL/HIGH/MEDIUM/LOW

### 3. Performance
- **Caching**: Cache LLM responses (see OS Agent)
- **Parallel Execution**: Downstream agents run in parallel
- **Minimal Calls**: One LLM call per agent if possible
- **Token Management**: Keep context within limits

### 4. Extensibility
- **Base Agent Interface**: Always extend BaseAgent
- **Standard Formats**: Use AgentChange for changes
- **Registry Pattern**: Register all agents centrally
- **Loose Coupling**: Agents don't know about specific downstreams

## Testing New Agents

```python
# Unit test
def test_my_agent():
    config = Config()
    kb = KnowledgeBaseManager(config)
    agent = MyNewAgent(config, kb)
    
    # Test direct analysis
    result = agent.analyze_changes(param1="value")
    assert 'changes' in result
    
    # Test upstream impact
    mock_changes = [
        {"component": "test", "description": "..."}
    ]
    impact = agent.analyze_upstream_impact(mock_changes)
    assert 'impacts' in impact

# Integration test
def test_agent_cascade():
    orchestrator = Orchestrator(config)
    my_agent = MyNewAgent(config, orchestrator.kb)
    orchestrator.add_agent(my_agent, upstream_agent_name="os-agent")
    
    analysis = orchestrator.analyze_simple("SLES 15 SP6", "SLES 15 SP7")
    
    assert 'my-new-agent' in analysis['downstream_impacts']
```

## Architecture Benefits

1. **Scalability**: Add new agents without changing existing code
2. **Maintainability**: Each agent is independent and testable
3. **Flexibility**: Support any dependency pattern
4. **Reusability**: Agents can be used in different configurations
5. **Clarity**: Clear data flow and responsibilities
6. **Automation**: Cascading happens automatically

## Future Enhancements

- **Async Execution**: Parallel downstream analysis
- **Conditional Propagation**: Only propagate relevant changes
- **Change Filtering**: Agents can filter what they receive
- **Bidirectional Communication**: Feedback from downstream to upstream
- **Dynamic Discovery**: Auto-discover compatible agents
- **Versioning**: Track agent versions and capabilities
