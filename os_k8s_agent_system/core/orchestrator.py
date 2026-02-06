"""
Orchestrator Agent
Coordinates multiple specialized agents for comprehensive analysis

Enhanced with scalable upstream-downstream pattern:
- Automatically wires agent dependencies
- Supports adding new agents dynamically
- Provides dependency visualization
"""

import logging
import json
import re
from typing import Dict, Any, List
from core.models import VersionChange, AnalysisReport, AgentMetadata
from core.knowledge_base import KnowledgeBaseManager
from core.base_agent import AgentRegistry
from core.document_store import get_document_store
from agents.os_agent import OSAgent
from agents.kubernetes_agent import KubernetesAgent
from core.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Coordinates multi-agent analysis workflow
    
    Enhanced Features:
    - Agent registry for dynamic agent management
    - Automatic dependency wiring
    - Cascading analysis (upstream -> downstream)
    - Extensible for new agent types
    """
    
    def __init__(self, config):
        self.config = config
        
        # Initialize agent registry
        self.registry = AgentRegistry()
        
        # Initialize knowledge base
        logger.info("Initializing knowledge base...")
        self.kb = KnowledgeBaseManager(config)
        
        # Initialize document store for internal documents
        logger.info("Initializing document store...")
        self.document_store = get_document_store()
        
        # Initialize agents
        logger.info("Initializing agents...")
        self.os_agent = OSAgent(config, self.kb)
        self.k8s_agent = KubernetesAgent(config, self.kb)
        
        # Register agents in registry
        self.registry.register(self.os_agent)
        self.registry.register(self.k8s_agent)
        
        # Wire up dependencies: OS Agent -> Kubernetes Agent
        self.os_agent.register_downstream(self.k8s_agent)
        
        # Initialize report generator
        self.report_gen = ReportGenerator()
        
        logger.info("Orchestrator ready")
        logger.info(f"Agent dependency graph:\n{self.registry.visualize_dependencies()}")
    
    def add_agent(self, agent, upstream_agent_name: str = None):
        """
        Dynamically add a new agent to the system
        
        Args:
            agent: The agent instance to add
            upstream_agent_name: Name of upstream agent this depends on (optional)
            
        Example:
            database_agent = DatabaseAgent(config, kb)
            orchestrator.add_agent(database_agent, upstream_agent_name="os-agent")
        """
        self.registry.register(agent)
        
        if upstream_agent_name:
            upstream = self.registry.get_agent(upstream_agent_name)
            if upstream:
                upstream.register_downstream(agent)
                logger.info(f"Wired: {upstream_agent_name} -> {agent.agent_name}")
            else:
                logger.warning(f"Upstream agent '{upstream_agent_name}' not found")
    
    def analyze_simple(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Simplified analysis - user just provides two version strings
        
        This triggers the full cascading analysis:
        1. OS Agent analyzes OS changes
        2. OS Agent automatically propagates to Kubernetes Agent
        3. Kubernetes Agent analyzes impacts
        4. Further agents in the chain analyze their impacts
        
        Args:
            from_version: Source OS version (e.g., "SLES 15 SP6")
            to_version: Target OS version (e.g., "SLES 15 SP7")
            
        Returns:
            Complete analysis with all agent results
        """
        logger.info(f"=== Starting Cascading Analysis: {from_version} → {to_version} ===")
        
        # Step 1: OS Agent analyzes (this automatically triggers downstream)
        print("\n" + "="*100)
        print("  MULTI-AGENT CASCADING ANALYSIS")
        print("="*100)
        print(f"\n🔍 Analyzing: {from_version} → {to_version}\n")
        
        # Show document store status
        docs = self.document_store.list_documents()
        if docs:
            print(f"📚 Internal Documents Loaded: {len(docs)}")
            by_cat = {}
            for d in docs:
                cat = d.get('category', 'general')
                by_cat[cat] = by_cat.get(cat, 0) + 1
            for cat, count in by_cat.items():
                print(f"   • {cat}: {count} document(s)")
        else:
            print("📚 Internal Documents: None loaded")
            print("   💡 Add company policies: python manage_docs.py add <file> --category kubernetes")
        
        print("\n📊 Agent Chain:")
        print(self.registry.visualize_dependencies())
        print("\n" + "="*100 + "\n")
        
        print("🤖 Step 1: OS Agent analyzing OS-level changes...")
        os_result = self.os_agent.analyze_changes(
            from_version=from_version,
            to_version=to_version
        )
        
        print(f"✅ OS Agent: Found {len(os_result.get('changes', []))} OS-level changes")
        
        # Downstream results are automatically included in os_result
        downstream = os_result.get('downstream_impacts', {})
        if downstream:
            print(f"\n✅ Downstream agents analyzed:")
            for agent_name, result in downstream.items():
                impact_count = len(result.get('impacts', []))
                print(f"   → {agent_name}: {impact_count} impacts identified")
        
        # Combine into final report
        final_report = {
            "upgrade": {
                "from_version": from_version,
                "to_version": to_version,
                "workload": "Kubernetes"
            },
            "os_analysis": {
                "changes": os_result.get('changes', []),
                "mitigation_steps": os_result.get('mitigation_steps', []),
                "recommendations": os_result.get('recommendations', []),
                "metadata": os_result.get('metadata', {}),
                "scrape_verification": os_result.get('scrape_verification', {})  # Screenshots and sources
            },
            "downstream_impacts": downstream,
            "agent_chain": self.registry.get_dependency_graph(),
            "document_sources": {
                "internal_documents": [
                    {"id": d["id"], "filename": d["filename"], "category": d["category"]}
                    for d in self.document_store.list_documents()
                ],
                "online_scraped": os_result.get('scrape_verification', {}).get('source_urls', [])
            }
        }
        
        # Print internal documents summary
        k8s_meta = downstream.get('kubernetes-agent', {}).get('metadata', {})
        if k8s_meta.get('internal_docs_used', 0) > 0:
            print(f"\n📄 Internal documents used by K8s Agent: {k8s_meta['internal_docs_used']}")
            for src in k8s_meta.get('internal_doc_sources', [])[:5]:
                print(f"   → {src}")
        
        # Print scrape verification summary
        scrape_info = os_result.get('scrape_verification', {})
        if scrape_info.get('screenshots'):
            print(f"\n📸 Screenshots captured: {len(scrape_info['screenshots'])}")
            for ss in scrape_info['screenshots'][:5]:  # Show first 5
                print(f"   → {ss.get('name')}: {ss.get('path')}")
        if scrape_info.get('source_urls'):
            print(f"\n🔗 Source URLs scraped: {len(scrape_info['source_urls'])}")
            for url in scrape_info['source_urls']:
                print(f"   → {url}")
        
        return final_report
    
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
