"""
Visual Browser Agent - Mino-Style with Rich Terminal UI
Shows real-time progress, screenshots, and extraction details
"""

import asyncio
import logging
import json
import time
import base64
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class AgentStep:
    """A single step in the agent workflow"""
    name: str
    status: str = "pending"  # pending, running, completed, failed
    start_time: float = 0.0
    end_time: float = 0.0
    details: str = ""
    data_extracted: int = 0


@dataclass
class AgentSession:
    """Tracks the entire agent session"""
    goal: str
    steps: List[AgentStep] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    extracted_content: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    current_url: str = ""
    status: str = "initializing"


class VisualProgressTracker:
    """Rich terminal UI for showing agent progress"""
    
    def __init__(self):
        self.session = None
        self.console = Console()
    
    def create_layout(self) -> Layout:
        """Create the main layout"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="steps", ratio=2),
            Layout(name="details", ratio=3)
        )
        return layout
    
    def render_header(self) -> Panel:
        """Render the header panel"""
        if not self.session:
            return Panel("Initializing...", title="🐟 Mino-Style Agent")
        
        status_color = {
            "initializing": "yellow",
            "running": "blue", 
            "completed": "green",
            "failed": "red"
        }.get(self.session.status, "white")
        
        header_text = Text()
        header_text.append("🐟 MINO-STYLE WEB AGENT", style="bold cyan")
        header_text.append(f"  |  Status: ", style="white")
        header_text.append(f"{self.session.status.upper()}", style=f"bold {status_color}")
        header_text.append(f"  |  URL: ", style="white")
        header_text.append(f"{self.session.current_url[:50]}...", style="dim")
        
        return Panel(header_text, box=box.DOUBLE)
    
    def render_steps(self) -> Panel:
        """Render the steps panel"""
        if not self.session:
            return Panel("No steps yet", title="📋 Steps")
        
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
        table.add_column("Status", width=8)
        table.add_column("Step", width=30)
        table.add_column("Time", width=8)
        table.add_column("Details", width=20)
        
        for step in self.session.steps:
            status_icon = {
                "pending": "⏳",
                "running": "🔄",
                "completed": "✅",
                "failed": "❌"
            }.get(step.status, "⚪")
            
            duration = ""
            if step.end_time > 0:
                duration = f"{step.end_time - step.start_time:.1f}s"
            elif step.start_time > 0:
                duration = f"{time.time() - step.start_time:.1f}s..."
            
            status_style = {
                "pending": "dim",
                "running": "bold yellow",
                "completed": "green",
                "failed": "red"
            }.get(step.status, "white")
            
            table.add_row(
                f"[{status_style}]{status_icon}[/{status_style}]",
                step.name[:30],
                duration,
                step.details[:20] if step.details else ""
            )
        
        return Panel(table, title="📋 Agent Steps", border_style="blue")
    
    def render_details(self) -> Panel:
        """Render the details/extraction panel"""
        if not self.session:
            return Panel("Waiting for data...", title="📊 Extracted Data")
        
        content = Text()
        
        # Show current activity
        running_steps = [s for s in self.session.steps if s.status == "running"]
        if running_steps:
            content.append("🔄 Currently: ", style="bold yellow")
            content.append(f"{running_steps[0].name}\n\n", style="yellow")
        
        # Show extracted content summary
        if self.session.extracted_content:
            content.append("📦 Extracted Content:\n", style="bold green")
            for key, value in self.session.extracted_content.items():
                if isinstance(value, str):
                    preview = value[:100] + "..." if len(value) > 100 else value
                    content.append(f"  • {key}: ", style="cyan")
                    content.append(f"{preview}\n", style="dim")
                elif isinstance(value, list):
                    content.append(f"  • {key}: ", style="cyan")
                    content.append(f"{len(value)} items\n", style="dim")
                elif isinstance(value, dict):
                    content.append(f"  • {key}: ", style="cyan")
                    content.append(f"{len(value)} fields\n", style="dim")
        
        # Show screenshots taken
        if self.session.screenshots:
            content.append(f"\n📸 Screenshots: {len(self.session.screenshots)}\n", style="bold magenta")
        
        return Panel(content, title="📊 Live Data", border_style="green")
    
    def render_footer(self) -> Panel:
        """Render the footer with progress"""
        if not self.session:
            return Panel("Starting...", title="Progress")
        
        completed = len([s for s in self.session.steps if s.status == "completed"])
        total = len(self.session.steps)
        
        elapsed = time.time() - self.session.start_time if self.session.start_time else 0
        
        footer_text = Text()
        footer_text.append(f"Progress: {completed}/{total} steps  |  ", style="white")
        footer_text.append(f"Elapsed: {elapsed:.1f}s  |  ", style="cyan")
        footer_text.append(f"Goal: {self.session.goal[:60]}...", style="dim")
        
        return Panel(footer_text, box=box.SIMPLE)
    
    def get_display(self) -> Layout:
        """Get the full display layout"""
        layout = self.create_layout()
        layout["header"].update(self.render_header())
        layout["steps"].update(self.render_steps())
        layout["details"].update(self.render_details())
        layout["footer"].update(self.render_footer())
        return layout


class VisualBrowserAgent:
    """
    Browser agent with rich visual feedback
    """
    
    def __init__(self, config):
        self.config = config
        self.browser = None
        self.page = None
        self.tracker = VisualProgressTracker()
        self.screenshot_dir = Path("./screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def _ensure_browser(self):
        """Initialize browser"""
        if self.browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self.browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                self.page = await self.browser.new_page()
            except ImportError:
                raise ImportError("Playwright not installed. Run: pip install playwright && playwright install chromium")
    
    def _add_step(self, name: str) -> AgentStep:
        """Add a new step to tracking"""
        step = AgentStep(name=name, status="running", start_time=time.time())
        self.tracker.session.steps.append(step)
        return step
    
    def _complete_step(self, step: AgentStep, details: str = ""):
        """Mark step as completed"""
        step.status = "completed"
        step.end_time = time.time()
        step.details = details
    
    def _fail_step(self, step: AgentStep, error: str):
        """Mark step as failed"""
        step.status = "failed"
        step.end_time = time.time()
        step.details = error[:50]
    
    async def run_with_visual(self, url: str, goal: str, extraction_config: Dict) -> Dict[str, Any]:
        """
        Run the agent with visual progress display
        """
        # Initialize session
        self.tracker.session = AgentSession(
            goal=goal,
            start_time=time.time(),
            status="running"
        )
        
        result = {}
        
        with Live(self.tracker.get_display(), refresh_per_second=4, console=console) as live:
            try:
                # Step 1: Initialize Browser
                step = self._add_step("Initialize Browser")
                live.update(self.tracker.get_display())
                await self._ensure_browser()
                self._complete_step(step, "Chromium ready")
                live.update(self.tracker.get_display())
                
                # Step 2: Navigate to URL
                step = self._add_step(f"Navigate to {url[:40]}...")
                self.tracker.session.current_url = url
                live.update(self.tracker.get_display())
                
                await self.page.goto(url, wait_until="networkidle", timeout=30000)
                self._complete_step(step, "Page loaded")
                live.update(self.tracker.get_display())
                
                # Step 3: Take Screenshot
                step = self._add_step("Capture Screenshot")
                live.update(self.tracker.get_display())
                
                timestamp = datetime.now().strftime("%H%M%S")
                screenshot_path = self.screenshot_dir / f"screenshot_{timestamp}.png"
                await self.page.screenshot(path=str(screenshot_path), full_page=False)
                self.tracker.session.screenshots.append(str(screenshot_path))
                self._complete_step(step, f"Saved: {screenshot_path.name}")
                live.update(self.tracker.get_display())
                
                # Step 4: Extract Page Title
                step = self._add_step("Extract Page Title")
                live.update(self.tracker.get_display())
                
                title = await self.page.title()
                self.tracker.session.extracted_content["title"] = title
                self._complete_step(step, title[:30])
                live.update(self.tracker.get_display())
                
                # Step 5: Extract Main Content
                step = self._add_step("Extract Main Content")
                live.update(self.tracker.get_display())
                
                content = await self.page.inner_text("body")
                content_preview = content[:500] + "..." if len(content) > 500 else content
                self.tracker.session.extracted_content["content_length"] = f"{len(content)} chars"
                self._complete_step(step, f"{len(content)} chars")
                live.update(self.tracker.get_display())
                
                # Step 6: Extract Specific Sections
                for section_name, selector in extraction_config.get("selectors", {}).items():
                    step = self._add_step(f"Extract: {section_name}")
                    live.update(self.tracker.get_display())
                    
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            texts = []
                            for el in elements[:20]:  # Limit to 20 elements
                                text = await el.inner_text()
                                if text.strip():
                                    texts.append(text.strip())
                            self.tracker.session.extracted_content[section_name] = texts
                            self._complete_step(step, f"{len(texts)} items")
                        else:
                            self._complete_step(step, "No items found")
                    except Exception as e:
                        self._fail_step(step, str(e))
                    
                    live.update(self.tracker.get_display())
                    await asyncio.sleep(0.1)  # Small delay for visual effect
                
                # Step 7: Extract removed/deprecated sections specifically
                step = self._add_step("Extract Removed Features Section")
                live.update(self.tracker.get_display())
                
                try:
                    # Try to find the removed features section
                    removed_section = await self.page.query_selector("#removed, [id*='removed'], section:has(h2:text('Removed'))")
                    if removed_section:
                        removed_text = await removed_section.inner_text()
                        self.tracker.session.extracted_content["removed_features"] = removed_text
                        self._complete_step(step, f"{len(removed_text)} chars")
                    else:
                        # Fallback: search for text containing "removed"
                        self._complete_step(step, "Section not found, using full content")
                except Exception as e:
                    self._fail_step(step, str(e))
                
                live.update(self.tracker.get_display())
                
                # Complete
                self.tracker.session.status = "completed"
                live.update(self.tracker.get_display())
                
                result = {
                    "url": url,
                    "title": title,
                    "content": content,
                    "extracted": self.tracker.session.extracted_content,
                    "screenshots": self.tracker.session.screenshots,
                    "steps_completed": len([s for s in self.tracker.session.steps if s.status == "completed"]),
                    "total_time": time.time() - self.tracker.session.start_time
                }
                
            except Exception as e:
                self.tracker.session.status = "failed"
                live.update(self.tracker.get_display())
                logger.error(f"Agent failed: {e}")
                result = {"error": str(e)}
            
            finally:
                # Keep display visible for a moment
                await asyncio.sleep(1)
        
        return result
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            await self._playwright.stop()
            self.browser = None
            self.page = None


class VisualSUSEAgent:
    """
    Visual SUSE Release Notes Agent
    """
    
    SUSE_URLS = {
        "SLES 15 SP6": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP6/index.html",
        "SLES 15 SP7": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP7/index.html",
    }
    
    def __init__(self, config, llm):
        self.config = config
        self.llm = llm
        self.browser_agent = VisualBrowserAgent(config)
    
    async def analyze_upgrade_visual(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Run visual analysis with rich terminal UI
        """
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🐟 MINO-STYLE VISUAL WEB AGENT[/bold cyan]\n"
            f"[white]Analyzing: {from_version} → {to_version}[/white]",
            border_style="cyan"
        ))
        console.print("\n")
        
        extraction_config = {
            "selectors": {
                "headings": "h1, h2, h3",
                "lists": "ul li, ol li",
                "warnings": ".admonition, .warning, .note, .important",
                "code_blocks": "code, pre",
            }
        }
        
        results = {}
        
        # Fetch FROM version
        console.print(f"[bold yellow]📥 Fetching {from_version} release notes...[/bold yellow]\n")
        from_url = self.SUSE_URLS.get(from_version, f"https://www.suse.com/releasenotes/x86_64/SUSE-SLES/{from_version.replace('SLES ', '').replace(' ', '-')}/index.html")
        
        from_result = await self.browser_agent.run_with_visual(
            url=from_url,
            goal=f"Extract release notes for {from_version}",
            extraction_config=extraction_config
        )
        results["from"] = from_result
        await self.browser_agent.close()
        
        console.print("\n")
        
        # Fetch TO version
        console.print(f"[bold yellow]📥 Fetching {to_version} release notes...[/bold yellow]\n")
        to_url = self.SUSE_URLS.get(to_version, f"https://www.suse.com/releasenotes/x86_64/SUSE-SLES/{to_version.replace('SLES ', '').replace(' ', '-')}/index.html")
        
        to_result = await self.browser_agent.run_with_visual(
            url=to_url,
            goal=f"Extract release notes for {to_version}",
            extraction_config=extraction_config
        )
        results["to"] = to_result
        await self.browser_agent.close()
        
        # Show extraction summary
        console.print("\n")
        summary_table = Table(title="📊 Extraction Summary", box=box.ROUNDED)
        summary_table.add_column("Version", style="cyan")
        summary_table.add_column("Content Size", style="green")
        summary_table.add_column("Time", style="yellow")
        summary_table.add_column("Screenshots", style="magenta")
        
        summary_table.add_row(
            from_version,
            f"{len(from_result.get('content', ''))} chars",
            f"{from_result.get('total_time', 0):.1f}s",
            str(len(from_result.get('screenshots', [])))
        )
        summary_table.add_row(
            to_version,
            f"{len(to_result.get('content', ''))} chars",
            f"{to_result.get('total_time', 0):.1f}s",
            str(len(to_result.get('screenshots', [])))
        )
        
        console.print(summary_table)
        console.print("\n")
        
        # Now analyze with LLM
        console.print("[bold blue]🧠 Analyzing with LLM...[/bold blue]\n")
        
        with console.status("[bold green]Processing with AI...") as status:
            analysis = await self._analyze_with_llm(
                from_version, to_version,
                from_result.get("content", ""),
                to_result.get("content", "")
            )
        
        return {
            "from_version": from_version,
            "to_version": to_version,
            "source_data": {
                "from_url": from_url,
                "to_url": to_url,
                "from_screenshots": from_result.get("screenshots", []),
                "to_screenshots": to_result.get("screenshots", []),
            },
            "extraction_stats": {
                "from_content_length": len(from_result.get("content", "")),
                "to_content_length": len(to_result.get("content", "")),
                "total_time": from_result.get("total_time", 0) + to_result.get("total_time", 0)
            },
            "analysis": analysis
        }
    
    async def _analyze_with_llm(self, from_ver: str, to_ver: str, from_content: str, to_content: str) -> Dict[str, Any]:
        """Analyze with LLM"""
        from langchain_core.prompts import ChatPromptTemplate
        
        # Limit content size
        from_content = from_content[:20000]
        to_content = to_content[:20000]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SUSE Linux expert. Extract ONLY factual information from the release notes.

IMPORTANT: Only report changes that are EXPLICITLY mentioned in the content. Do not make assumptions.

Return valid JSON:
{{
  "removed_packages": [
    {{"package": "name", "replacement": "alternative or null", "description": "exact text from notes"}}
  ],
  "deprecated_packages": [
    {{"package": "name", "description": "exact text from notes"}}
  ],
  "new_features": [
    {{"feature": "name", "description": "brief description"}}
  ],
  "breaking_changes": [
    {{"component": "name", "change": "what changed", "impact": "HIGH/MEDIUM/LOW"}}
  ],
  "k8s_impacts": [
    {{"component": "kubelet/container-runtime/etc", "impact": "description"}}
  ]
}}"""),
            ("human", """Compare these SUSE release notes and extract changes:

=== {from_version} ===
{from_content}

=== {to_version} ===
{to_content}

Extract ONLY explicitly mentioned:
1. Removed packages (look for "removed", "no longer available")
2. Deprecated packages (look for "deprecated", "will be removed")  
3. New features
4. Breaking changes
5. Kubernetes/container impacts

Return ONLY JSON.""")
        ])
        
        chain = prompt | self.llm
        
        try:
            result = chain.invoke({
                "from_version": from_ver,
                "to_version": to_ver,
                "from_content": from_content,
                "to_content": to_content
            })
            
            import re
            response = result.content.strip()
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"error": str(e)}


def run_async(coro):
    """Run async function"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
