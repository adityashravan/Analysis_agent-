"""
Orchestrator Agent
Coordinates multiple specialized agents for comprehensive analysis
"""

import logging
import json
import re
from typing import Dict, Any, List
from core.models import VersionChange, AnalysisReport, AgentMetadata
from core.knowledge_base import KnowledgeBaseManager
from agents.os_agent import OSAgent
from agents.kubernetes_agent import KubernetesAgent
from core.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates multi-agent analysis workflow
    """
    
    def __init__(self, config):
        self.config = config
        
        # Initialize knowledge base
        logger.info("Initializing knowledge base...")
        self.kb = KnowledgeBaseManager(config)
        
        # Initialize agents
        logger.info("Initializing agents...")
        self.os_agent = OSAgent(config, self.kb)
        self.k8s_agent = KubernetesAgent(config, self.kb)
        
        # Initialize report generator
        self.report_gen = ReportGenerator()
        
        logger.info("Orchestrator ready")
    
    def load_knowledge_base(self, sources: Dict[str, Any]):
        """
        Load knowledge base from various sources
        
        sources = {
            "pdfs": ["path/to/doc.pdf"],
            "text_files": ["path/to/notes.txt"],
            "web_pages": ["https://docs.suse.com/..."],
            "directories": ["path/to/docs/"]
        }
        """
        logger.info("Loading knowledge base...")
        
        stats = {"total_chunks": 0, "sources": 0}
        
        # PDFs
        for pdf_path in sources.get("pdfs", []):
            try:
                chunks = self.kb.ingest_pdf(pdf_path)
                stats["total_chunks"] += chunks
                stats["sources"] += 1
                logger.info(f"✓ Loaded PDF: {pdf_path} ({chunks} chunks)")
            except Exception as e:
                logger.error(f"✗ Failed to load PDF {pdf_path}: {e}")
        
        # Text files
        for file_path in sources.get("text_files", []):
            try:
                chunks = self.kb.ingest_text_file(file_path)
                stats["total_chunks"] += chunks
                stats["sources"] += 1
                logger.info(f"✓ Loaded text file: {file_path} ({chunks} chunks)")
            except Exception as e:
                logger.error(f"✗ Failed to load text file {file_path}: {e}")
        
        # Web pages
        for url in sources.get("web_pages", []):
            try:
                chunks = self.kb.ingest_web_page(url)
                stats["total_chunks"] += chunks
                stats["sources"] += 1
                logger.info(f"✓ Loaded web page: {url} ({chunks} chunks)")
            except Exception as e:
                logger.error(f"✗ Failed to load web page {url}: {e}")
        
        # Directories
        for directory in sources.get("directories", []):
            try:
                dir_stats = self.kb.ingest_directory(directory)
                total = sum(dir_stats.values())
                stats["total_chunks"] += total
                stats["sources"] += len(dir_stats)
                logger.info(f"✓ Loaded directory: {directory} ({total} chunks from {len(dir_stats)} files)")
            except Exception as e:
                logger.error(f"✗ Failed to load directory {directory}: {e}")
        
        logger.info(f"Knowledge base loaded: {stats['sources']} sources, {stats['total_chunks']} chunks")
        return stats
    
    def analyze_version_change(self, version_change: VersionChange) -> Dict[str, Any]:
        """
        Orchestrate complete version change analysis
        """
        logger.info(f"Starting analysis: {version_change.from_version} → {version_change.to_version}")
        
        # Step 1: OS Agent analyzes version changes (returns structured JSON)
        logger.info("Step 1: OS Agent analyzing version changes...")
        os_analysis = self.os_agent.analyze_version_change(version_change)
        
        # Step 2: Kubernetes Agent analyzes impacts (takes structured input, returns structured JSON)
        logger.info("Step 2: Kubernetes Agent analyzing impacts...")
        k8s_analysis = self.k8s_agent.analyze_os_impact(os_analysis)
        
        # Step 3: Combine structured results
        logger.info("Step 3: Combining structured results...")
        final_report = self._combine_structured_analysis(
            version_change,
            os_analysis,
            k8s_analysis
        )
        
        return final_report
    
    def _combine_structured_analysis(
        self,
        version_change: VersionChange,
        os_analysis: Dict[str, Any],
        k8s_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine structured agent outputs into final report
        Both inputs are already structured JSON from the agents
        """
        report = {
            "upgrade": {
                "from_version": version_change.from_version,
                "to_version": version_change.to_version,
                "workload": version_change.workload
            },
            "agent_metadata": {
                "agent_name": "suse-os-agent",
                "domain": "operating-system",
                "confidence": 0.95,
                "evidence": os_analysis.get("evidence_sources", [])
            },
            "breaking_changes": os_analysis.get("breaking_changes", []),
            "kubernetes_impact": k8s_analysis.get("kubernetes_impact", []),
            "mitigation_steps": os_analysis.get("mitigation_steps", []),
            "recommendations": os_analysis.get("recommendations", [])
        }
        
        return report
    
    def generate_report(self, analysis: Dict[str, Any], output_formats: List[str] = None):
        """
        Generate reports in specified formats
        """
        if output_formats is None:
            output_formats = ["console", "json", "markdown"]
        
        results = {}
        
        if "console" in output_formats:
            self.report_gen.generate_console_report(analysis)
            results["console"] = "displayed"
        
        if "json" in output_formats:
            json_path = self.report_gen.generate_json_report(analysis)
            results["json"] = json_path
        
        if "markdown" in output_formats:
            md_path = self.report_gen.generate_markdown_report(analysis)
            results["markdown"] = md_path
        
        return results
