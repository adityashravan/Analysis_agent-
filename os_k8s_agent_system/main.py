"""
Main entry point for OS & Kubernetes Version Impact Analysis System
"""

import logging
import sys
import argparse
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
    Main execution flow - Simplified user experience
    User just specifies two OS versions!
    """
    print("\n" + "="*100, flush=True)
    print("  OS & KUBERNETES VERSION IMPACT ANALYSIS SYSTEM", flush=True)
    print("  Multi-Agent Architecture with Upstream-Downstream Pattern", flush=True)
    print("="*100 + "\n", flush=True)
    
    # Load configuration
    logger.info("Loading configuration...")
    print("🔧 Step 1: Loading configuration...", flush=True)
    config = Config()
    
    try:
        config.validate()
        print("✅ Configuration validated", flush=True)
        print(f"   LLM Provider: {config.llm_provider}", flush=True)
        print(f"   Model: {config.llm_model}", flush=True)

        # Display API key fallback status
        if config.fallback_api_keys:
            print(f"   🔑 Backup API Keys: {len(config.fallback_api_keys)} available", flush=True)
            print(f"   💡 Fallback: Enabled (will auto-switch if primary key exhausts)\n", flush=True)
        else:
            print(f"   ⚠️  No backup API keys configured\n", flush=True)
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
    print("✅ Multi-agent system initialized", flush=True)
    print(f"   Agents ready: OS Agent, Kubernetes Agent", flush=True)
    print(f"   Dependency chain: OS Agent → Kubernetes Agent\n", flush=True)
    
    # Skip knowledge base for now - use LLM's built-in knowledge
    print("📚 Step 3: Knowledge Base - Using LLM's built-in knowledge", flush=True)
    print("-" * 100, flush=True)
    print("   (To add custom sources, uncomment the knowledge_sources section below)\n", flush=True)
    
    # ============================================
    # USER INPUT - Get OS versions from user or command line
    # ============================================
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='OS & Kubernetes Version Impact Analysis')
    parser.add_argument('--from', dest='from_version', type=str, help='Source OS version (e.g., "SLES 15 SP6")')
    parser.add_argument('--to', dest='to_version', type=str, help='Target OS version (e.g., "SLES 15 SP7")')
    args, _ = parser.parse_known_args()
    
    # Check if versions provided via command line
    if args.from_version and args.to_version:
        from_version = args.from_version
        to_version = args.to_version
        print("=" * 100)
        print("  USING COMMAND-LINE ARGUMENTS")
        print("=" * 100)
    else:
        # Interactive mode - get from user input
        print("=" * 100)
        print("  USER INPUT")
        print("=" * 100)
        print("\nPlease provide the OS version details:\n")

        # Get current OS version
        from_version = input("Enter current OS version (e.g., SLES 15 SP6): ").strip()
        if not from_version:
            from_version = "SLES 15 SP6"  # Default fallback
            print(f"   No input provided. Using default: {from_version}")

        # Get new OS version
        to_version = input("Enter new OS version (e.g., SLES 15 SP7): ").strip()
        if not to_version:
            to_version = "SLES 15 SP7"  # Default fallback
            print(f"   No input provided. Using default: {to_version}")

    print(f"\n🔍 Version Change Analysis:")
    print(f"   From: {from_version}")
    print(f"   To:   {to_version}")
    print("-" * 100 + "\n")
    
    # Run simplified analysis - automatically cascades through all agents!
    print("🚀 Running Multi-Agent Cascading Analysis...")
    print("   This may take 30-60 seconds...\n")
    
    try:
        logger.info("Starting cascading analysis...")
        analysis = orchestrator.analyze_simple(from_version, to_version)
        
        # Generate reports
        print("\n" + "="*100)
        print("  ANALYSIS COMPLETE - GENERATING DETAILED REPORTS")
        print("="*100 + "\n")
        
        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
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
