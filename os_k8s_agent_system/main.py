"""
Main entry point for OS & Kubernetes Version Impact Analysis System
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.models import Config, VersionChange
from core.orchestrator import Orchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main execution flow - Generates comprehensive Markdown report
    """
    print("\n" + "="*100, flush=True)
    print("  OS & KUBERNETES VERSION IMPACT ANALYSIS SYSTEM", flush=True)
    print("  Multi-Agent Architecture for Cross-Layer Compatibility Analysis", flush=True)
    print("="*100 + "\n", flush=True)
    
    # Load configuration
    logger.info("Loading configuration...")
    print("🔧 Step 1: Loading configuration...", flush=True)
    config = Config()
    
    try:
        config.validate()
        print("✅ Configuration validated", flush=True)
        print(f"   LLM Provider: {config.llm_provider}", flush=True)
        print(f"   Model: {config.llm_model}\n", flush=True)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}", flush=True)
        print("\nPlease set up your .env file with required API keys:", flush=True)
        print("  1. Ensure .env file exists with your API key", flush=True)
        print("  2. Add your OpenAI or Anthropic API key", flush=True)
        print("  3. Run the script again\n", flush=True)
        return
    
    # Initialize orchestrator
    logger.info("Initializing orchestrator...")
    print("🤖 Step 2: Initializing multi-agent system...", flush=True)
    orchestrator = Orchestrator(config)
    print("✅ Multi-agent system initialized\n", flush=True)
    
    # Skip knowledge base for now - use LLM's built-in knowledge
    print("📚 Step 3: Knowledge Base - Using LLM's built-in knowledge", flush=True)
    print("-" * 100, flush=True)
    print("   (To add custom sources, uncomment the knowledge_sources section in main.py)\n", flush=True)
    
    # Define version change to analyze
    version_change = VersionChange(
        layer="OS",
        from_version="SLES 15 SP6",
        to_version="SLES 15 SP7",
        workload="Kubernetes"
    )
    
    print(f"🔍 Analyzing Version Change:")
    print(f"   From: {version_change.from_version}")
    print(f"   To:   {version_change.to_version}")
    print(f"   Workload: {version_change.workload}")
    print("-" * 100 + "\n")
    
    # Run analysis
    print("🤖 Running Multi-Agent Analysis...")
    print("   This may take 30-60 seconds...\n")
    
    try:
        logger.info("Starting multi-agent analysis...")
        analysis = orchestrator.analyze_version_change(version_change)
        
        # Generate reports
        print("\n" + "="*100)
        print("  ANALYSIS COMPLETE - GENERATING DETAILED REPORTS")
        print("="*100 + "\n")
        
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"SUSE_SP6_to_SP7_Analysis_{timestamp}"
        
        # Generate all report formats
        results = orchestrator.generate_report(
            analysis,
            output_formats=["console", "json", "markdown"]
        )
        
        print("\n" + "="*100)
        print("  ✅ REPORTS GENERATED SUCCESSFULLY")
        print("="*100 + "\n")
        
        print("📄 Generated Reports:")
        for format_type, path in results.items():
            if format_type == "console":
                print(f"   • Console: Displayed above")
            else:
                print(f"   • {format_type.upper()}: {path}")
        
        # Highlight the main markdown report
        if "markdown" in results:
            print(f"\n📋 **Main Report**: {results['markdown']}")
            print(f"   Open this file for detailed analysis documentation\n")
        
        print("="*100)
        print("  Analysis session completed successfully!")
        print("="*100 + "\n")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\n❌ Analysis Error: {e}\n")
        print("💡 Troubleshooting:")
        print("   • Check your API key in .env")
        print("   • Ensure internet connection")
        print("   • Check API quota/limits\n")
        return


if __name__ == "__main__":
    main()
