"""
Example: How to Use the Enhanced Multi-Agent System

This example demonstrates:
1. Simple usage - just specify two OS versions
2. How to add new agents dynamically
3. How agents cascade automatically
4. Extensibility for new domains
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.models import Config
from core.orchestrator import Orchestrator
from agents.database_agent import DatabaseAgent


def example_1_simple_usage():
    """
    Example 1: Simplest usage - just two version strings
    
    The system automatically:
    - Analyzes OS changes
    - Propagates to Kubernetes Agent
    - Returns comprehensive analysis
    """
    print("\n" + "="*100)
    print("EXAMPLE 1: Simple Usage")
    print("="*100 + "\n")
    
    # Setup
    config = Config()
    config.validate()
    orchestrator = Orchestrator(config)
    
    # Just specify two versions - that's it!
    analysis = orchestrator.analyze_simple(
        from_version="SLES 15 SP6",
        to_version="SLES 15 SP7"
    )
    
    # Results include OS changes + Kubernetes impacts
    os_changes = analysis['os_analysis']['changes']
    k8s_impacts = analysis['downstream_impacts'].get('kubernetes-agent', {}).get('impacts', [])
    
    print(f"\n✅ Found {len(os_changes)} OS changes")
    print(f"✅ Found {len(k8s_impacts)} Kubernetes impacts")
    print("\nDone! The agents automatically cascaded through the dependency chain.")


def example_2_add_database_agent():
    """
    Example 2: Adding a new agent to the system
    
    Shows how to dynamically extend the system with new agents.
    The database agent will automatically receive OS/K8s changes.
    """
    print("\n" + "="*100)
    print("EXAMPLE 2: Adding Database Agent")
    print("="*100 + "\n")
    
    # Setup
    config = Config()
    config.validate()
    orchestrator = Orchestrator(config)
    
    # Create database agent
    print("➕ Creating Database Agent...")
    db_agent = DatabaseAgent(config, orchestrator.kb)
    
    # Add to system - wire to OS Agent as upstream
    print("🔗 Wiring: OS Agent → Database Agent...")
    orchestrator.add_agent(db_agent, upstream_agent_name="os-agent")
    
    # Now when we analyze, database agent also gets triggered!
    print("\n🚀 Running analysis with Database Agent included...")
    analysis = orchestrator.analyze_simple(
        from_version="SLES 15 SP6",
        to_version="SLES 15 SP7"
    )
    
    # Check results from all agents
    downstream = analysis.get('downstream_impacts', {})
    
    print("\n✅ Analysis complete! Results from:")
    print("   - OS Agent (root)")
    for agent_name in downstream.keys():
        print(f"   - {agent_name} (downstream)")
    
    # Database impacts
    db_impacts = downstream.get('database-agent', {}).get('impacts', [])
    print(f"\n📊 Database Agent found {len(db_impacts)} potential impacts")


def example_3_custom_agent_chain():
    """
    Example 3: Creating a custom agent chain
    
    Demonstrates building a more complex dependency graph:
    OS Agent → Kubernetes Agent → App Agent
             → Database Agent
    """
    print("\n" + "="*100)
    print("EXAMPLE 3: Custom Agent Chain")
    print("="*100 + "\n")
    
    config = Config()
    config.validate()
    orchestrator = Orchestrator(config)
    
    # Add database agent (parallel to K8s)
    db_agent = DatabaseAgent(config, orchestrator.kb)
    orchestrator.add_agent(db_agent, upstream_agent_name="os-agent")
    
    # Visualize the dependency graph
    print("📊 Agent Dependency Graph:")
    print(orchestrator.registry.visualize_dependencies())
    
    print("\n💡 This structure means:")
    print("   1. OS Agent analyzes OS changes")
    print("   2. Changes propagate to BOTH Kubernetes and Database agents (parallel)")
    print("   3. Each analyzes impacts in their domain")
    print("   4. Results are aggregated automatically")
    
    print("\n🚀 Running analysis through full chain...")
    analysis = orchestrator.analyze_simple("SLES 15 SP6", "SLES 15 SP7")
    
    print("\n✅ Complete! Check 'downstream_impacts' in the analysis for all agent results.")


def example_4_accessing_results():
    """
    Example 4: How to access and use analysis results
    """
    print("\n" + "="*100)
    print("EXAMPLE 4: Accessing Results")
    print("="*100 + "\n")
    
    config = Config()
    config.validate()
    orchestrator = Orchestrator(config)
    
    analysis = orchestrator.analyze_simple("SLES 15 SP6", "SLES 15 SP7")
    
    # Access OS-level changes
    print("📊 OS-Level Changes:")
    for change in analysis['os_analysis']['changes'][:3]:  # Show first 3
        print(f"   - {change.get('component')}: {change.get('severity')}")
    
    # Access Kubernetes impacts
    print("\n📊 Kubernetes Impacts:")
    k8s_impacts = analysis['downstream_impacts'].get('kubernetes-agent', {}).get('impacts', [])
    for impact in k8s_impacts[:3]:  # Show first 3
        print(f"   - {impact.get('k8s_component')}: {impact.get('severity')}")
    
    # Access mitigation steps
    print("\n🔧 Mitigation Steps:")
    steps = analysis['os_analysis']['mitigation_steps'][:3]
    for step in steps:
        print(f"   - {step.get('action')}")
    
    print("\n✅ Results are structured and easy to work with!")


def example_5_simple_script():
    """
    Example 5: Minimal script for quick analysis
    
    Copy this for a quick start!
    """
    print("\n" + "="*100)
    print("EXAMPLE 5: Minimal Script (Copy This!)")
    print("="*100 + "\n")
    
    print("""
# Minimal script - just 6 lines!

from core.models import Config
from core.orchestrator import Orchestrator

config = Config()
orchestrator = Orchestrator(config)
analysis = orchestrator.analyze_simple("SLES 15 SP6", "SLES 15 SP7")

# That's it! analysis contains full OS + K8s impact analysis.
""")


if __name__ == "__main__":
    print("\n" + "="*100)
    print("  MULTI-AGENT SYSTEM - USAGE EXAMPLES")
    print("="*100)
    
    # Run examples
    # Uncomment the ones you want to try:
    
    # example_1_simple_usage()
    # example_2_add_database_agent()
    # example_3_custom_agent_chain()
    # example_4_accessing_results()
    example_5_simple_script()
    
    print("\n" + "="*100)
    print("  Done! Modify this file to try different examples.")
    print("="*100 + "\n")
