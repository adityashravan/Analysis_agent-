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
    """System configuration - Optimized for free/low-cost APIs (Mino-inspired)"""
    
    # Free tier compatible models on OpenRouter
    FREE_MODELS = [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "deepseek/deepseek-chat:free",
        "mistralai/mistral-small-24b-instruct-2501:free"
    ]
    
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")  # Backup API key
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai")
        self.llm_model = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-exp:free")
        self.vector_store = os.getenv("VECTOR_STORE", "chromadb")
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

        # Mino-inspired efficiency settings
        self.enable_caching = os.getenv("ENABLE_CACHING", "true").lower() == "true"
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.use_streaming = os.getenv("USE_STREAMING", "true").lower() == "true"

        # Embedding model - use smaller/free compatible
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        # API key tracking for fallback
        self.current_api_key = self.openai_api_key
        self.fallback_api_keys = []
        if self.google_api_key:
            self.fallback_api_keys.append(self.google_api_key)
        
    def validate(self) -> bool:
        """Validate configuration"""
        if self.llm_provider == "openai" and not self.openai_api_key and not self.fallback_api_keys:
            raise ValueError("OPENAI_API_KEY or GOOGLE_API_KEY (fallback) not set")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        return True

    def switch_to_fallback_key(self):
        """Switch to the next available fallback API key"""
        if self.fallback_api_keys:
            old_key_preview = self.current_api_key[:20] if self.current_api_key else "None"
            self.current_api_key = self.fallback_api_keys.pop(0)
            self.openai_api_key = self.current_api_key
            new_key_preview = self.current_api_key[:20]
            print(f"⚠️  Switched to fallback API key: {old_key_preview}... -> {new_key_preview}...")
            return True
        return False

    def get_active_api_key(self):
        """Get the currently active API key"""
        return self.current_api_key
    
    def get_model_info(self) -> str:
        """Get model information for display"""
        is_free = any(free in self.llm_model for free in [":free", "free"])
        return f"{self.llm_model} ({'FREE' if is_free else 'PAID'})"
