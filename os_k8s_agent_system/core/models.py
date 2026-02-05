"""
Multi-Agent System for OS & Kubernetes Version Impact Analysis
Architecture: Specialized agents coordinated by an orchestrator
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Data Models
class VersionChange(BaseModel):
    """Model for version change request"""
    layer: str = Field(description="Layer type: OS, Kubernetes, Runtime, etc.")
    from_version: str = Field(description="Source version")
    to_version: str = Field(description="Target version")
    workload: Optional[str] = Field(default="Kubernetes", description="Target workload")


class BreakingChange(BaseModel):
    """Model for a breaking change"""
    component: str
    change_type: str  # breaking, behavioral, deprecated
    description: str
    affected_components: List[str]
    impact_severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    evidence_sources: List[str] = Field(default_factory=list)


class MitigationStep(BaseModel):
    """Model for mitigation action"""
    step: str
    action: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    timing: str  # pre-upgrade, during-upgrade, post-upgrade
    estimated_time: Optional[str] = None


class ImpactAnalysis(BaseModel):
    """Model for impact analysis on a component"""
    component: str
    impact_description: str
    required_actions: List[str]
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW


class AgentMetadata(BaseModel):
    """Metadata about agent analysis"""
    agent_name: str
    domain: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_sources: List[str]
    analysis_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisReport(BaseModel):
    """Complete analysis report"""
    version_change: VersionChange
    agent_metadata: AgentMetadata
    breaking_changes: List[BreakingChange]
    impact_analysis: List[ImpactAnalysis]
    mitigation_steps: List[MitigationStep]
    recommendations: List[str]
    confidence_score: float


# Configuration
class Config:
    """System configuration"""
    
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai")
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.vector_store = os.getenv("VECTOR_STORE", "chromadb")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        
    def validate(self) -> bool:
        """Validate configuration"""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return True
