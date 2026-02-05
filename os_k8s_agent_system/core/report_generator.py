"""
Report Generator
Creates beautiful tabular reports with comprehensive analysis
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box


class ReportGenerator:
    """
    Generates comprehensive reports in multiple formats
    - Console (Rich tables)
    - JSON
    - HTML
    - Markdown
    """
    
    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.console = Console()
    
    def generate_console_report(self, analysis: Dict[str, Any]):
        """Generate beautiful console output"""
        
        self.console.print("\n")
        self.console.print("="*100, style="bold blue")
        self.console.print(
            f"   OS & KUBERNETES VERSION IMPACT ANALYSIS",
            style="bold white on blue",
            justify="center"
        )
        self.console.print("="*100, style="bold blue")
        
        # Version Info
        upgrade = analysis.get("upgrade", {})
        self.console.print(f"\n📊 [bold]Upgrade Analysis:[/bold]")
        self.console.print(f"   From: [cyan]{upgrade.get('from_version')}[/cyan]")
        self.console.print(f"   To:   [green]{upgrade.get('to_version')}[/green]")
        self.console.print(f"   Workload: [yellow]{upgrade.get('workload')}[/yellow]")
        
        # Agent Metadata
        metadata = analysis.get("agent_metadata", {})
        self.console.print(f"\n🤖 [bold]Analysis Metadata:[/bold]")
        self.console.print(f"   Agent: {metadata.get('agent_name')}")
        self.console.print(f"   Domain: {metadata.get('domain')}")
        self.console.print(f"   Confidence: {metadata.get('confidence', 0):.0%}")
        self.console.print(f"   Evidence Sources: {len(metadata.get('evidence', []))}")
        
        # Breaking Changes Table
        breaking_changes = analysis.get("breaking_changes", [])
        if breaking_changes:
            self.console.print(f"\n\n🔥 [bold red]BREAKING CHANGES ({len(breaking_changes)})[/bold red]\n")
            
            table = Table(
                title="Breaking & Behavioral Changes",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            
            table.add_column("Severity", style="bold", width=10)
            table.add_column("Component", style="cyan", width=25)
            table.add_column("Type", width=12)
            table.add_column("Description", width=40)
            table.add_column("K8s Impact", style="yellow", width=20)
            
            # Sort by severity
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            sorted_changes = sorted(
                breaking_changes,
                key=lambda x: severity_order.get(x.get("impact_severity", "LOW"), 4)
            )
            
            for change in sorted_changes:
                severity = change.get("impact_severity", "")
                severity_style = {
                    "CRITICAL": "[bold red]🔴 CRITICAL[/bold red]",
                    "HIGH": "[bold orange1]🟠 HIGH[/bold orange1]",
                    "MEDIUM": "[bold yellow]🟡 MEDIUM[/bold yellow]",
                    "LOW": "[bold green]🟢 LOW[/bold green]"
                }.get(severity, severity)
                
                table.add_row(
                    severity_style,
                    change.get("component", ""),
                    change.get("change_type", ""),
                    change.get("description", "")[:100] + "..." if len(change.get("description", "")) > 100 else change.get("description", ""),
                    ", ".join(change.get("affected_k8s_components", [])[:2])
                )
            
            self.console.print(table)
        
        # Kubernetes Impact Table
        k8s_impact = analysis.get("kubernetes_impact", [])
        if k8s_impact:
            self.console.print(f"\n\n☸️  [bold blue]KUBERNETES IMPACT ({len(k8s_impact)})[/bold blue]\n")
            
            table = Table(
                title="Kubernetes Component Impact Analysis",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold cyan"
            )
            
            table.add_column("Component", style="bold cyan", width=25)
            table.add_column("Impact Description", width=45)
            table.add_column("Actions Required", style="green", width=30)
            
            for impact in k8s_impact:
                actions = impact.get("required_actions", [])
                actions_text = f"• " + "\n• ".join(actions[:3])
                if len(actions) > 3:
                    actions_text += f"\n... +{len(actions)-3} more"
                
                table.add_row(
                    impact.get("k8s_component", ""),
                    impact.get("impact_description", ""),
                    actions_text
                )
            
            self.console.print(table)
        
        # Mitigation Steps Table
        mitigation = analysis.get("mitigation_steps", [])
        if mitigation:
            self.console.print(f"\n\n🛠️  [bold green]MITIGATION STEPS ({len(mitigation)})[/bold green]\n")
            
            table = Table(
                title="Required Mitigation Actions",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold green"
            )
            
            table.add_column("Step", style="bold", width=6)
            table.add_column("Priority", width=10)
            table.add_column("Timing", width=15)
            table.add_column("Action", width=60)
            
            for step in mitigation:
                priority_style = {
                    "CRITICAL": "[bold red]CRITICAL[/bold red]",
                    "HIGH": "[bold orange1]HIGH[/bold orange1]",
                    "MEDIUM": "[bold yellow]MEDIUM[/bold yellow]",
                    "LOW": "[bold green]LOW[/bold green]"
                }.get(step.get("priority", ""), step.get("priority", ""))
                
                table.add_row(
                    step.get("step", ""),
                    priority_style,
                    step.get("timing", ""),
                    step.get("action", "")
                )
            
            self.console.print(table)
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            self.console.print(f"\n\n💡 [bold yellow]RECOMMENDATIONS[/bold yellow]\n")
            for i, rec in enumerate(recommendations, 1):
                self.console.print(f"   {i}. {rec}")
        
        self.console.print("\n" + "="*100 + "\n")
    
    def generate_json_report(self, analysis: Dict[str, Any], filename: str = None) -> str:
        """Generate JSON report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        return str(filepath)
    
    def generate_markdown_report(self, analysis: Dict[str, Any], filename: str = None) -> str:
        """Generate comprehensive Markdown report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        lines = []
        
        # Header
        lines.append("# OS & Kubernetes Version Impact Analysis Report\n\n")
        lines.append("---\n\n")
        
        # Executive Summary
        upgrade = analysis.get("upgrade", {})
        lines.append("## Executive Summary\n\n")
        lines.append(f"**Upgrade Path**: `{upgrade.get('from_version')}` → `{upgrade.get('to_version')}`\n\n")
        lines.append(f"**Target Workload**: {upgrade.get('workload')}\n\n")
        lines.append(f"**Analysis Date**: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}\n\n")
        
        # Quick Stats
        breaking_changes = analysis.get("breaking_changes", [])
        k8s_impact = analysis.get("kubernetes_impact", [])
        mitigation = analysis.get("mitigation_steps", [])
        recommendations = analysis.get("recommendations", [])
        
        critical_count = sum(1 for c in breaking_changes if c.get('impact_severity') == 'CRITICAL')
        high_count = sum(1 for c in breaking_changes if c.get('impact_severity') == 'HIGH')
        
        lines.append("### 📊 Analysis Summary\n\n")
        lines.append(f"- **Total Breaking Changes**: {len(breaking_changes)}\n")
        lines.append(f"- **Critical Issues**: {critical_count} 🔴\n")
        lines.append(f"- **High Priority Issues**: {high_count} 🟠\n")
        lines.append(f"- **Kubernetes Components Affected**: {len(k8s_impact)}\n")
        lines.append(f"- **Required Mitigation Steps**: {len(mitigation)}\n")
        lines.append(f"- **Strategic Recommendations**: {len(recommendations)}\n\n")
        
        # Agent Metadata
        metadata = analysis.get("agent_metadata", {})
        lines.append("### 🤖 Analysis Metadata\n\n")
        lines.append(f"- **Agent**: {metadata.get('agent_name', 'N/A')}\n")
        lines.append(f"- **Domain**: {metadata.get('domain', 'N/A')}\n")
        lines.append(f"- **Confidence Score**: {metadata.get('confidence', 0):.0%}\n")
        lines.append(f"- **Evidence Sources**: {len(metadata.get('evidence', []))}\n\n")
        
        if metadata.get('evidence'):
            lines.append("**Documentation Sources**:\n")
            for source in metadata.get('evidence', []):
                lines.append(f"- {source}\n")
            lines.append("\n")
        
        lines.append("---\n\n")
        
        # Breaking Changes - Detailed
        if breaking_changes:
            lines.append(f"## 🔥 Breaking Changes ({len(breaking_changes)})\n\n")
            lines.append("### Overview Table\n\n")
            
            # Create detailed table
            table_data = []
            for change in breaking_changes:
                severity = change.get('impact_severity', '')
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(severity, '')
                table_data.append({
                    'Severity': f"{emoji} {severity}",
                    'Component': change.get('component', '')[:40],
                    'Type': change.get('change_type', ''),
                    'K8s Components': ', '.join(change.get('affected_k8s_components', [])[:3])
                })
            
            df = pd.DataFrame(table_data)
            lines.append(df.to_markdown(index=False))
            lines.append("\n\n")
            
            # Detailed descriptions
            lines.append("### Detailed Analysis\n\n")
            for i, change in enumerate(breaking_changes, 1):
                severity = change.get('impact_severity', '')
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(severity, '')
                
                lines.append(f"#### {i}. {change.get('component', 'Unknown Component')} {emoji}\n\n")
                lines.append(f"**Change Type**: {change.get('change_type', 'N/A')}\n\n")
                lines.append(f"**Impact Severity**: {severity}\n\n")
                lines.append(f"**Description**:\n\n")
                lines.append(f"{change.get('description', 'No description available.')}\n\n")
                
                affected = change.get('affected_k8s_components', [])
                if affected:
                    lines.append(f"**Affected Kubernetes Components**:\n")
                    for comp in affected:
                        lines.append(f"- {comp}\n")
                    lines.append("\n")
                
                lines.append("---\n\n")
        
        # Kubernetes Impact
        if k8s_impact:
            lines.append(f"## ☸️ Kubernetes Impact Analysis ({len(k8s_impact)})\n\n")
            
            for i, impact in enumerate(k8s_impact, 1):
                lines.append(f"### {i}. {impact.get('k8s_component', 'Unknown Component')}\n\n")
                
                lines.append(f"**Impact Description**:\n\n")
                lines.append(f"{impact.get('impact_description', 'No description available.')}\n\n")
                
                actions = impact.get('required_actions', [])
                if actions:
                    lines.append(f"**Required Actions**:\n\n")
                    for j, action in enumerate(actions, 1):
                        lines.append(f"{j}. {action}\n")
                    lines.append("\n")
                
                lines.append("---\n\n")
        
        # Mitigation Steps
        if mitigation:
            lines.append(f"## 🛠️ Mitigation Steps ({len(mitigation)})\n\n")
            lines.append("### Action Plan\n\n")
            
            # Group by timing
            pre_upgrade = [s for s in mitigation if s.get('timing') == 'pre-upgrade']
            during_upgrade = [s for s in mitigation if s.get('timing') == 'during-upgrade']
            post_upgrade = [s for s in mitigation if s.get('timing') == 'post-upgrade']
            
            if pre_upgrade:
                lines.append("#### Pre-Upgrade Actions\n\n")
                for step in pre_upgrade:
                    priority = step.get('priority', '')
                    emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(priority, '')
                    lines.append(f"**Step {step.get('step')}** {emoji} *{priority} Priority*\n\n")
                    lines.append(f"{step.get('action', '')}\n\n")
            
            if during_upgrade:
                lines.append("#### During-Upgrade Actions\n\n")
                for step in during_upgrade:
                    priority = step.get('priority', '')
                    emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(priority, '')
                    lines.append(f"**Step {step.get('step')}** {emoji} *{priority} Priority*\n\n")
                    lines.append(f"{step.get('action', '')}\n\n")
            
            if post_upgrade:
                lines.append("#### Post-Upgrade Actions\n\n")
                for step in post_upgrade:
                    priority = step.get('priority', '')
                    emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(priority, '')
                    lines.append(f"**Step {step.get('step')}** {emoji} *{priority} Priority*\n\n")
                    lines.append(f"{step.get('action', '')}\n\n")
            
            lines.append("---\n\n")
        
        # Recommendations
        if recommendations:
            lines.append(f"## 💡 Strategic Recommendations ({len(recommendations)})\n\n")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}\n\n")
            lines.append("---\n\n")
        
        # Footer
        lines.append("## Report Information\n\n")
        lines.append(f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"- **System**: Multi-Agent OS & Kubernetes Analysis System\n")
        lines.append(f"- **Format**: Markdown Report v1.0\n\n")
        lines.append("---\n\n")
        lines.append("*This report was automatically generated by the AI-powered Multi-Agent Analysis System.*\n")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        return str(filepath)
    
    def generate_all_formats(self, analysis: Dict[str, Any], base_name: str = None):
        """Generate reports in all formats"""
        results = {}
        
        # Console
        self.generate_console_report(analysis)
        
        # JSON
        json_path = self.generate_json_report(analysis, f"{base_name}.json" if base_name else None)
        results['json'] = json_path
        
        # Markdown
        md_path = self.generate_markdown_report(analysis, f"{base_name}.md" if base_name else None)
        results['markdown'] = md_path
        
        return results
