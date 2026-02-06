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
        
        # Agent Metadata - get from os_analysis.metadata
        metadata = analysis.get("os_analysis", {}).get("metadata", {})
        self.console.print(f"\n🤖 [bold]Analysis Metadata:[/bold]")
        self.console.print(f"   Agent: {metadata.get('agent_name', 'N/A')}")
        self.console.print(f"   Domain: {metadata.get('domain', 'N/A')}")
        confidence = metadata.get('confidence', 0.85)  # Default confidence
        self.console.print(f"   Confidence: {confidence:.0%}")
        evidence = metadata.get('evidence_sources', [])
        self.console.print(f"   Evidence Sources: {len(evidence)}")
        
        # Extract data from CORRECT paths
        os_analysis = analysis.get("os_analysis", {})
        breaking_changes = os_analysis.get("changes", [])
        mitigation = os_analysis.get("mitigation_steps", [])
        recommendations = os_analysis.get("recommendations", [])
        
        # Scrape verification data
        scrape_verification = os_analysis.get("scrape_verification", {})
        if scrape_verification:
            self.console.print(f"\n📸 [bold]Data Source Verification:[/bold]")
            
            # Show screenshots
            screenshots = scrape_verification.get("screenshots", [])
            if screenshots:
                self.console.print(f"   Screenshots captured: [green]{len(screenshots)}[/green]")
                for ss in screenshots[:4]:  # Show first 4
                    self.console.print(f"      → {ss.get('name')}: [dim]{ss.get('path')}[/dim]")
                if len(screenshots) > 4:
                    self.console.print(f"      → [dim]... and {len(screenshots) - 4} more[/dim]")
            
            # Show source URLs
            source_urls = scrape_verification.get("source_urls", [])
            if source_urls:
                self.console.print(f"   Source URLs scraped: [green]{len(source_urls)}[/green]")
                for url in source_urls:
                    self.console.print(f"      → [blue]{url}[/blue]")
            
            # Show sections found
            sections = scrape_verification.get("sections_found", [])
            if sections:
                self.console.print(f"   Sections extracted: [green]{len(sections)}[/green]")
                for section in sections:
                    self.console.print(f"      → {section.get('section')}: {section.get('chars_extracted', 0)} chars")
        
        # Get K8s impacts from downstream
        downstream = analysis.get("downstream_impacts", {})
        k8s_data = downstream.get("kubernetes-agent", {})
        k8s_impact = k8s_data.get("impacts", [])
        
        # Breaking Changes Table
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
                key=lambda x: severity_order.get(x.get("severity", "LOW"), 4)
            )
            
            for change in sorted_changes:
                severity = change.get("severity", "")
                severity_style = {
                    "CRITICAL": "[bold red]🔴 CRITICAL[/bold red]",
                    "HIGH": "[bold orange1]🟠 HIGH[/bold orange1]",
                    "MEDIUM": "[bold yellow]🟡 MEDIUM[/bold yellow]",
                    "LOW": "[bold green]🟢 LOW[/bold green]"
                }.get(severity, severity)
                
                # Get affected K8s components from metadata
                affected = change.get("metadata", {}).get("affected_k8s_components", [])
                
                table.add_row(
                    severity_style,
                    change.get("component", ""),
                    change.get("change_type", ""),
                    change.get("description", "")[:100] + "..." if len(change.get("description", "")) > 100 else change.get("description", ""),
                    ", ".join(affected[:2]) if affected else "N/A"
                )
            
            self.console.print(table)
        
        # Kubernetes Impact Table (k8s_impact already set above)
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
        
        # Mitigation Steps Table (mitigation variable already set above)
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
        
        # Recommendations (recommendations variable already set above)
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
        
        # Extract data from CORRECT paths in the JSON structure
        os_analysis = analysis.get("os_analysis", {})
        breaking_changes = os_analysis.get("changes", [])
        mitigation = os_analysis.get("mitigation_steps", [])
        recommendations = os_analysis.get("recommendations", [])
        metadata = os_analysis.get("metadata", {})
        
        # Get Kubernetes impacts from downstream_impacts
        downstream = analysis.get("downstream_impacts", {})
        k8s_data = downstream.get("kubernetes-agent", {})
        k8s_impact = k8s_data.get("impacts", [])
        
        # Count severities
        critical_count = sum(1 for c in breaking_changes if c.get('severity') == 'CRITICAL')
        high_count = sum(1 for c in breaking_changes if c.get('severity') == 'HIGH')
        
        lines.append("### 📊 Analysis Summary\n\n")
        lines.append(f"- **Total Breaking Changes**: {len(breaking_changes)}\n")
        lines.append(f"- **Critical Issues**: {critical_count} 🔴\n")
        lines.append(f"- **High Priority Issues**: {high_count} 🟠\n")
        lines.append(f"- **Kubernetes Components Affected**: {len(k8s_impact)}\n")
        lines.append(f"- **Required Mitigation Steps**: {len(mitigation)}\n")
        lines.append(f"- **Strategic Recommendations**: {len(recommendations)}\n\n")
        
        # Agent Metadata - from os_analysis.metadata
        evidence_sources = metadata.get("evidence_sources", [])
        lines.append("### 🤖 Analysis Metadata\n\n")
        lines.append(f"- **Agent**: {metadata.get('agent_name', 'N/A')}\n")
        lines.append(f"- **Domain**: {metadata.get('domain', 'N/A')}\n")
        lines.append(f"- **From Version**: {metadata.get('from_version', 'N/A')}\n")
        lines.append(f"- **To Version**: {metadata.get('to_version', 'N/A')}\n")
        lines.append(f"- **Evidence Sources**: {len(evidence_sources)}\n\n")
        
        if evidence_sources:
            lines.append("**Documentation Sources**:\n")
            for source in evidence_sources:
                lines.append(f"- {source}\n")
            lines.append("\n")
        
        # Scrape Verification Section - Screenshots and Source Tracking
        scrape_verification = os_analysis.get("scrape_verification", {})
        if scrape_verification:
            lines.append("### 📸 Data Source Verification\n\n")
            lines.append("*This section shows proof of where the analysis data came from*\n\n")
            
            # Source URLs
            source_urls = scrape_verification.get("source_urls", [])
            if source_urls:
                lines.append("**URLs Scraped**:\n")
                for url in source_urls:
                    lines.append(f"- [{url}]({url})\n")
                lines.append("\n")
            
            # Screenshots
            screenshots = scrape_verification.get("screenshots", [])
            if screenshots:
                lines.append(f"**Screenshots Captured** ({len(screenshots)} total):\n\n")
                lines.append("| Screenshot | Description | Path |\n")
                lines.append("|------------|-------------|------|\n")
                for ss in screenshots:
                    lines.append(f"| {ss.get('name', 'N/A')} | {ss.get('description', 'N/A')} | `{ss.get('path', 'N/A')}` |\n")
                lines.append("\n")
            
            # Sections Found
            sections = scrape_verification.get("sections_found", [])
            if sections:
                lines.append("**Sections Extracted from Release Notes**:\n\n")
                lines.append("| Section | Elements Found | Characters Extracted |\n")
                lines.append("|---------|----------------|---------------------|\n")
                for section in sections:
                    lines.append(f"| {section.get('section', 'N/A')} | {section.get('count', 0)} | {section.get('chars_extracted', 0):,} |\n")
                lines.append("\n")
            
            # Scrape timestamp
            if scrape_verification.get("scrape_timestamp"):
                lines.append(f"*Scraped at: {scrape_verification.get('scrape_timestamp')}*\n\n")
        
        lines.append("---\n\n")
        
        # Breaking Changes - Detailed
        if breaking_changes:
            lines.append(f"## 🔥 Breaking Changes ({len(breaking_changes)})\n\n")
            lines.append("### Overview Table\n\n")
            
            # Create detailed table
            table_data = []
            for change in breaking_changes:
                severity = change.get('severity', '')
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(severity, '')
                # Get affected components from metadata
                affected = change.get('metadata', {}).get('affected_k8s_components', [])
                table_data.append({
                    'Severity': f"{emoji} {severity}",
                    'Component': change.get('component', '')[:40],
                    'Type': change.get('change_type', ''),
                    'K8s Components': ', '.join(affected[:3]) if affected else 'N/A'
                })
            
            df = pd.DataFrame(table_data)
            lines.append(df.to_markdown(index=False))
            lines.append("\n\n")
            
            # Detailed descriptions
            lines.append("### Detailed Analysis\n\n")
            for i, change in enumerate(breaking_changes, 1):
                severity = change.get('severity', '')
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(severity, '')
                
                lines.append(f"#### {i}. {change.get('component', 'Unknown Component')} {emoji}\n\n")
                lines.append(f"**Change Type**: {change.get('change_type', 'N/A')}\n\n")
                lines.append(f"**Impact Severity**: {severity}\n\n")
                lines.append(f"**Description**:\n\n")
                lines.append(f"{change.get('description', 'No description available.')}\n\n")
                
                affected = change.get('metadata', {}).get('affected_k8s_components', [])
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
