"""
Precision Browser Agent - Mino-Style with Section-Specific Screenshots
Navigates to specific sections, takes targeted screenshots, extracts exact content
"""

import asyncio
import logging
import json
import time
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.syntax import Syntax
from rich import box

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ExtractedItem:
    """A single extracted item with full details"""
    name: str
    item_type: str  # removed, deprecated, moved, changed
    description: str
    replacement: Optional[str] = None
    source_text: str = ""  # Original text from page


@dataclass 
class AgentStep:
    """A single step in the agent workflow"""
    name: str
    status: str = "pending"
    start_time: float = 0.0
    end_time: float = 0.0
    details: str = ""
    extracted_text: str = ""


@dataclass
class AgentSession:
    """Tracks the entire agent session"""
    goal: str
    steps: List[AgentStep] = field(default_factory=list)
    screenshots: List[Dict[str, str]] = field(default_factory=list)  # {path, section, description}
    extracted_items: List[ExtractedItem] = field(default_factory=list)
    raw_sections: Dict[str, str] = field(default_factory=dict)
    start_time: float = 0.0
    current_url: str = ""
    current_section: str = ""
    status: str = "initializing"


class PrecisionTracker:
    """Rich UI with extracted content display"""
    
    def __init__(self):
        self.session = None
        self.console = Console()
    
    def create_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="main", ratio=1),
            Layout(name="extracted", size=12),
            Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="steps", ratio=1),
            Layout(name="live_content", ratio=2)
        )
        return layout
    
    def render_header(self) -> Panel:
        if not self.session:
            return Panel("Initializing...", title="🐟 Agent")
        
        status_color = {"initializing": "yellow", "running": "blue", "completed": "green", "failed": "red"}.get(self.session.status, "white")
        
        text = Text()
        text.append("🐟 PRECISION WEB AGENT", style="bold cyan")
        text.append(f"\n   Status: ", style="white")
        text.append(f"{self.session.status.upper()}", style=f"bold {status_color}")
        text.append(f"  |  Section: ", style="white")
        text.append(f"{self.session.current_section or 'None'}", style="yellow")
        text.append(f"\n   URL: ", style="white")
        text.append(f"{self.session.current_url}", style="dim cyan")
        
        return Panel(text, box=box.DOUBLE, border_style="cyan")
    
    def render_steps(self) -> Panel:
        if not self.session:
            return Panel("Waiting...", title="📋 Steps")
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("S", width=3)
        table.add_column("Step", width=25)
        table.add_column("Info", width=15)
        
        for step in self.session.steps[-8:]:  # Show last 8 steps
            icon = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}.get(step.status, "⚪")
            style = {"pending": "dim", "running": "bold yellow", "completed": "green", "failed": "red"}.get(step.status, "white")
            
            duration = ""
            if step.end_time > 0:
                duration = f"{step.end_time - step.start_time:.1f}s"
            elif step.start_time > 0:
                duration = f"{time.time() - step.start_time:.1f}s"
            
            table.add_row(
                f"[{style}]{icon}[/{style}]",
                f"[{style}]{step.name[:25]}[/{style}]",
                f"[dim]{duration}[/dim]"
            )
        
        return Panel(table, title="📋 Steps", border_style="blue")
    
    def render_live_content(self) -> Panel:
        if not self.session:
            return Panel("Waiting for content...", title="📄 Live Content")
        
        content = Text()
        
        # Show current step's extracted text
        running = [s for s in self.session.steps if s.status == "running"]
        if running and running[0].extracted_text:
            content.append("📝 Extracting:\n", style="bold yellow")
            preview = running[0].extracted_text[:300]
            content.append(preview + "..." if len(running[0].extracted_text) > 300 else preview, style="dim")
        
        # Show screenshots taken
        if self.session.screenshots:
            content.append(f"\n\n📸 Screenshots ({len(self.session.screenshots)}):\n", style="bold magenta")
            for ss in self.session.screenshots[-3:]:
                content.append(f"  • {ss.get('section', 'page')}: ", style="cyan")
                content.append(f"{ss.get('path', '').split('/')[-1]}\n", style="dim")
        
        return Panel(content, title="📄 Live Content", border_style="green")
    
    def render_extracted(self) -> Panel:
        if not self.session or not self.session.extracted_items:
            return Panel("[dim]No items extracted yet...[/dim]", title="🔍 Extracted Items")
        
        table = Table(show_header=True, header_style="bold", box=box.SIMPLE, expand=True)
        table.add_column("Type", width=10, style="yellow")
        table.add_column("Package/Feature", width=25, style="cyan")
        table.add_column("Details", width=40)
        table.add_column("Replacement", width=15, style="green")
        
        for item in self.session.extracted_items[-6:]:  # Last 6 items
            type_style = {"removed": "red", "deprecated": "yellow", "moved": "blue", "changed": "magenta"}.get(item.item_type, "white")
            table.add_row(
                f"[{type_style}]{item.item_type.upper()}[/{type_style}]",
                item.name[:25],
                item.description[:40] + "..." if len(item.description) > 40 else item.description,
                item.replacement or "-"
            )
        
        return Panel(table, title=f"🔍 Extracted Items ({len(self.session.extracted_items)})", border_style="yellow")
    
    def render_footer(self) -> Panel:
        if not self.session:
            return Panel("Starting...", box=box.SIMPLE)
        
        completed = len([s for s in self.session.steps if s.status == "completed"])
        total = len(self.session.steps)
        elapsed = time.time() - self.session.start_time if self.session.start_time else 0
        
        text = Text()
        text.append(f"Progress: {completed}/{total} steps", style="white")
        text.append(f"  |  Time: {elapsed:.1f}s", style="cyan")
        text.append(f"  |  Items: {len(self.session.extracted_items)}", style="green")
        text.append(f"  |  Screenshots: {len(self.session.screenshots)}", style="magenta")
        
        return Panel(text, box=box.SIMPLE)
    
    def get_display(self) -> Layout:
        layout = self.create_layout()
        layout["header"].update(self.render_header())
        layout["steps"].update(self.render_steps())
        layout["live_content"].update(self.render_live_content())
        layout["extracted"].update(self.render_extracted())
        layout["footer"].update(self.render_footer())
        return layout


class PrecisionBrowserAgent:
    """
    Precision Browser Agent - Takes section-specific screenshots and extracts exact content
    """
    
    def __init__(self, config):
        self.config = config
        self.browser = None
        self.page = None
        self.tracker = PrecisionTracker()
        self.screenshot_dir = Path("./screenshots")
        self.screenshot_dir.mkdir(exist_ok=True)
    
    async def _ensure_browser(self):
        if self.browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.page = await self.browser.new_page()
            await self.page.set_viewport_size({"width": 1280, "height": 900})
    
    def _add_step(self, name: str) -> AgentStep:
        step = AgentStep(name=name, status="running", start_time=time.time())
        self.tracker.session.steps.append(step)
        return step
    
    def _complete_step(self, step: AgentStep, details: str = "", extracted: str = ""):
        step.status = "completed"
        step.end_time = time.time()
        step.details = details
        step.extracted_text = extracted
    
    def _fail_step(self, step: AgentStep, error: str):
        step.status = "failed"
        step.end_time = time.time()
        step.details = error[:50]
    
    def _parse_removed_features(self, text: str) -> List[ExtractedItem]:
        """Parse the removed features section and extract individual items"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Pattern: "package has been removed" or "package has been moved"
            # redis has been removed in SLES 15 SP7...Use valkey instead
            removed_match = re.search(r'^[•\-\*]?\s*(\S+)\s+has been removed', line, re.IGNORECASE)
            if removed_match:
                pkg = removed_match.group(1)
                replacement = None
                repl_match = re.search(r'Use\s+(\S+)\s+instead', line, re.IGNORECASE)
                if repl_match:
                    replacement = repl_match.group(1)
                items.append(ExtractedItem(
                    name=pkg,
                    item_type="removed",
                    description=line,
                    replacement=replacement,
                    source_text=line
                ))
                continue
            
            # Pattern: "package has been moved to..."
            moved_match = re.search(r'^[•\-\*]?\s*(\S+)\s+has been moved', line, re.IGNORECASE)
            if moved_match:
                pkg = moved_match.group(1)
                replacement = None
                repl_match = re.search(r'Use\s+(\S+)\s+instead', line, re.IGNORECASE)
                if repl_match:
                    replacement = repl_match.group(1)
                items.append(ExtractedItem(
                    name=pkg,
                    item_type="moved",
                    description=line,
                    replacement=replacement,
                    source_text=line
                ))
                continue
            
            # Pattern: "X and Y packages have been moved/removed"
            multi_match = re.search(r'^[•\-\*]?\s*(\S+)\s+and\s+(\S+).*(?:moved|removed|deprecated)', line, re.IGNORECASE)
            if multi_match:
                item_type = "removed" if "removed" in line.lower() else "moved" if "moved" in line.lower() else "deprecated"
                items.append(ExtractedItem(
                    name=f"{multi_match.group(1)}, {multi_match.group(2)}",
                    item_type=item_type,
                    description=line,
                    source_text=line
                ))
                continue
            
            # Pattern: "removed the X feature from Y"
            feature_match = re.search(r'removed\s+the\s+(\S+)\s+feature', line, re.IGNORECASE)
            if feature_match:
                items.append(ExtractedItem(
                    name=feature_match.group(1),
                    item_type="removed",
                    description=line,
                    source_text=line
                ))
                continue
            
            # Pattern: "PHP 7.4 has been removed" or similar version patterns
            version_match = re.search(r'^[•\-\*]?\s*([\w\s]+\d+\.?\d*)\s+has been removed', line, re.IGNORECASE)
            if version_match:
                items.append(ExtractedItem(
                    name=version_match.group(1).strip(),
                    item_type="removed",
                    description=line,
                    source_text=line
                ))
                continue
        
        return items
    
    def _parse_deprecated_features(self, text: str) -> List[ExtractedItem]:
        """Parse deprecated features from SUSE release notes"""
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Skip section headers and titles
            if line.startswith('#') or line.startswith('9.') or 'features and packages' in line.lower():
                continue
            
            # Must contain deprecated/removal keywords
            if 'deprecated' not in line.lower() and 'will be removed' not in line.lower():
                continue
            
            # Pattern 1: "X and Y drivers have been deprecated" 
            # e.g., "netiucv and lcs drivers have been deprecated and will be removed in SLES 16."
            multi_match = re.search(r'^[•\-\*]?\s*(?:The\s+)?(.+?)\s+(?:drivers?|packages?|images?)\s+(?:have been|has been|will be)\s+deprecated', line, re.IGNORECASE)
            if multi_match:
                name = multi_match.group(1).strip()
                items.append(ExtractedItem(
                    name=name,
                    item_type="deprecated",
                    description=line,
                    source_text=line
                ))
                continue
            
            # Pattern 2: "The X will be deprecated and removed"
            # e.g., "The 2MB OVMF image will be deprecated and removed in SLES 16.1."
            the_match = re.search(r'^[•\-\*]?\s*The\s+(.+?)\s+(?:will be|is|has been)\s+deprecated', line, re.IGNORECASE)
            if the_match:
                name = the_match.group(1).strip()
                items.append(ExtractedItem(
                    name=name,
                    item_type="deprecated",
                    description=line,
                    source_text=line
                ))
                continue
            
            # Pattern 3: Generic - any line with deprecated keyword, extract first meaningful phrase
            # Fallback for other formats
            generic_match = re.search(r'^[•\-\*]?\s*(.+?)\s+(?:is|are|has been|have been|will be)\s+deprecated', line, re.IGNORECASE)
            if generic_match:
                name = generic_match.group(1).strip()
                if len(name) > 3 and len(name) < 100:  # Sanity check
                    items.append(ExtractedItem(
                        name=name,
                        item_type="deprecated",
                        description=line,
                        source_text=line
                    ))
        
        return items
    
    async def extract_release_notes(self, url: str, version: str, live) -> Dict[str, Any]:
        """Extract release notes with section-specific screenshots"""
        
        self.tracker.session = AgentSession(
            goal=f"Extract {version} release notes",
            start_time=time.time(),
            status="running",
            current_url=url
        )
        
        result = {"url": url, "version": version, "sections": {}, "items": []}
        
        try:
            # Step 1: Initialize Browser
            step = self._add_step("Initialize Browser")
            live.update(self.tracker.get_display())
            await self._ensure_browser()
            self._complete_step(step, "Ready")
            live.update(self.tracker.get_display())
            
            # Step 2: Navigate to main page
            step = self._add_step(f"Navigate to {version} page")
            live.update(self.tracker.get_display())
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            self._complete_step(step, "Loaded")
            live.update(self.tracker.get_display())
            
            # Step 3: Take full page screenshot
            step = self._add_step("Screenshot: Full Page")
            live.update(self.tracker.get_display())
            timestamp = datetime.now().strftime("%H%M%S")
            ss_path = self.screenshot_dir / f"{version.replace(' ', '_')}_full_{timestamp}.png"
            await self.page.screenshot(path=str(ss_path), full_page=False)
            self.tracker.session.screenshots.append({"path": str(ss_path), "section": "full_page"})
            self._complete_step(step, ss_path.name)
            live.update(self.tracker.get_display())
            
            # Step 4: Navigate to #removed section
            step = self._add_step("Navigate to Removed Section")
            self.tracker.session.current_section = "Removed Features"
            live.update(self.tracker.get_display())
            
            # Try to navigate to the removed section using anchor
            await self.page.goto(f"{url}#removed", wait_until="networkidle", timeout=15000)
            await asyncio.sleep(0.5)
            
            # Scroll the section into view
            try:
                await self.page.evaluate("""
                    const el = document.querySelector('#removed, [id*="removed"], h2:has(a[id*="removed"])');
                    if (el) el.scrollIntoView({behavior: 'instant', block: 'start'});
                """)
            except:
                pass
            
            self._complete_step(step, "Section found")
            live.update(self.tracker.get_display())
            
            # Step 5: Screenshot the Removed Section
            step = self._add_step("Screenshot: Removed Section")
            live.update(self.tracker.get_display())
            await asyncio.sleep(0.3)
            
            ss_path = self.screenshot_dir / f"{version.replace(' ', '_')}_removed_{timestamp}.png"
            await self.page.screenshot(path=str(ss_path), full_page=False)
            self.tracker.session.screenshots.append({"path": str(ss_path), "section": "removed_features"})
            self._complete_step(step, ss_path.name)
            live.update(self.tracker.get_display())
            
            # Step 6: Extract Removed Section Text
            step = self._add_step("Extract Removed Section Text")
            live.update(self.tracker.get_display())
            
            removed_text = ""
            try:
                # Try multiple selectors for the removed section
                selectors = [
                    "#removed",
                    "section:has(h2 a[id*='removed'])",
                    "#cha-removed",
                    "div:has(> h2:text-matches('Removed', 'i'))"
                ]
                
                for selector in selectors:
                    try:
                        element = await self.page.query_selector(selector)
                        if element:
                            removed_text = await element.inner_text()
                            if len(removed_text) > 100:
                                break
                    except:
                        continue
                
                # Fallback: Get text from visible area around "removed" heading
                if len(removed_text) < 100:
                    full_text = await self.page.inner_text("body")
                    # Find the section starting with "Removed"
                    match = re.search(r'(9\.?\s*Removed.*?)(?=10\.|$)', full_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        removed_text = match.group(1)
                
                step.extracted_text = removed_text[:500]
                self.tracker.session.raw_sections["removed"] = removed_text
                
                # Parse extracted items
                items = self._parse_removed_features(removed_text)
                self.tracker.session.extracted_items.extend(items)
                result["items"].extend([vars(i) for i in items])
                
                self._complete_step(step, f"{len(items)} items found", removed_text[:200])
                
            except Exception as e:
                self._complete_step(step, f"Error: {str(e)[:30]}")
                logger.warning(f"Removed extraction error: {e}")
            
            live.update(self.tracker.get_display())
            
            # Step 7: Navigate to Deprecated Section
            step = self._add_step("Navigate to Deprecated Section")
            self.tracker.session.current_section = "Deprecated Features"
            live.update(self.tracker.get_display())
            
            try:
                # Scroll down to find deprecated section
                await self.page.evaluate("""
                    const el = document.querySelector('[id*="deprecated"], h3:text-matches("Deprecated", "i")');
                    if (el) el.scrollIntoView({behavior: 'instant', block: 'start'});
                """)
                await asyncio.sleep(0.3)
                self._complete_step(step, "Section found")
            except Exception as e:
                self._complete_step(step, f"Scroll error: {str(e)[:20]}")
            
            live.update(self.tracker.get_display())
            
            # Step 8: Screenshot Deprecated Section
            step = self._add_step("Screenshot: Deprecated Section")
            live.update(self.tracker.get_display())
            
            try:
                timestamp = datetime.now().strftime("%H%M%S")
                ss_path = self.screenshot_dir / f"{version.replace(' ', '_')}_deprecated_{timestamp}.png"
                await self.page.screenshot(path=str(ss_path), full_page=False)
                self.tracker.session.screenshots.append({"path": str(ss_path), "section": "deprecated_features"})
                self._complete_step(step, ss_path.name)
            except Exception as e:
                self._complete_step(step, f"Screenshot error: {str(e)[:20]}")
            
            live.update(self.tracker.get_display())
            
            # Step 9: Extract Deprecated Text
            step = self._add_step("Extract Deprecated Section Text")
            live.update(self.tracker.get_display())
            
            try:
                full_text = await self.page.inner_text("body")
                
                # The page has TOC at top and actual content below
                # Look for the ACTUAL deprecated section (not TOC)
                deprecated_text = ""
                
                # Simple and direct approach: Find content between "9.2 Deprecated" header and "10 Obtaining"
                # The actual section starts around character 70000+ in the page
                
                # First, find where the actual section is (by looking for "The following features")
                section_start = full_text.find("The following features and packages are deprecated and will be removed")
                if section_start > 0:
                    # Find the end (next section)
                    section_end = full_text.find("10 Obtaining source code", section_start)
                    if section_end < 0:
                        section_end = section_start + 500  # Fallback
                    
                    deprecated_text = full_text[section_start:section_end].strip()
                    logger.info(f"Found deprecated section: {len(deprecated_text)} chars")
                
                if deprecated_text and len(deprecated_text) > 50:
                    self.tracker.session.raw_sections["deprecated"] = deprecated_text
                    
                    items = self._parse_deprecated_features(deprecated_text)
                    self.tracker.session.extracted_items.extend(items)
                    result["items"].extend([vars(i) for i in items])
                    
                    self._complete_step(step, f"{len(items)} deprecated items", deprecated_text[:150])
                else:
                    self._complete_step(step, "No deprecated section found")
            except Exception as e:
                self._complete_step(step, f"Error: {str(e)[:30]}")
                logger.warning(f"Deprecated extraction error: {e}")
            
            live.update(self.tracker.get_display())
            
            # Complete
            self.tracker.session.status = "completed"
            live.update(self.tracker.get_display())
            
            result["sections"] = self.tracker.session.raw_sections
            result["screenshots"] = self.tracker.session.screenshots
            result["total_items"] = len(self.tracker.session.extracted_items)
            
        except Exception as e:
            self.tracker.session.status = "failed"
            live.update(self.tracker.get_display())
            result["error"] = str(e)
        
        return result
    
    async def close(self):
        if self.browser:
            await self.browser.close()
            await self._playwright.stop()
            self.browser = None


class PrecisionSUSEAgent:
    """Main agent for precise SUSE release notes extraction - Analyzes BOTH versions"""
    
    URLS = {
        "SLES 15 SP6": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP6/index.html",
        "SLES 15 SP7": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP7/index.html",
    }
    
    def __init__(self, config, llm):
        self.config = config
        self.llm = llm
    
    async def analyze_upgrade(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Run precision analysis on BOTH versions and compare"""
        
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🎯 PRECISION WEB AGENT[/bold cyan]\n"
            "[white]Section-specific screenshots + Exact content extraction[/white]\n"
            f"[dim]Comparing: {from_version} ↔ {to_version}[/dim]",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        results = {"from_version": from_version, "to_version": to_version}
        
        # ============ EXTRACT FROM VERSION (SP6) ============
        console.print(f"\n[bold yellow]📥 STEP 1: Extracting {from_version} release notes...[/bold yellow]\n")
        
        agent_from = PrecisionBrowserAgent(self.config)
        from_url = self.URLS.get(from_version)
        
        with Live(agent_from.tracker.get_display(), refresh_per_second=4, console=console) as live:
            from_result = await agent_from.extract_release_notes(from_url, from_version, live)
            await asyncio.sleep(0.5)
        
        await agent_from.close()
        results["from_extraction"] = from_result
        
        # ============ EXTRACT TO VERSION (SP7) ============
        console.print(f"\n[bold yellow]📥 STEP 2: Extracting {to_version} release notes...[/bold yellow]\n")
        
        agent_to = PrecisionBrowserAgent(self.config)
        to_url = self.URLS.get(to_version)
        
        with Live(agent_to.tracker.get_display(), refresh_per_second=4, console=console) as live:
            to_result = await agent_to.extract_release_notes(to_url, to_version, live)
            await asyncio.sleep(0.5)
        
        await agent_to.close()
        results["to_extraction"] = to_result
        
        # ============ COMPARE VERSIONS ============
        console.print(f"\n[bold blue]🔄 STEP 3: Comparing {from_version} vs {to_version}...[/bold blue]\n")
        
        from_items = {item.get("name"): item for item in from_result.get("items", [])}
        to_items = {item.get("name"): item for item in to_result.get("items", [])}
        
        # Find NEW items in TO version (not in FROM)
        new_in_to = []
        for name, item in to_items.items():
            if name not in from_items:
                new_in_to.append(item)
        
        # Find items REMOVED from FROM version (in FROM but not in TO removed list)
        # This is actually the removed items in TO version
        
        results["comparison"] = {
            "from_total_items": len(from_items),
            "to_total_items": len(to_items),
            "new_removals_in_to": new_in_to,  # Items newly marked as removed in SP7
        }
        
        # ============ DISPLAY RESULTS ============
        console.print("\n")
        console.print(Panel.fit("[bold green]✅ EXTRACTION & COMPARISON COMPLETE[/bold green]", border_style="green"))
        
        # Summary table
        summary = Table(title="📊 Extraction Summary", box=box.ROUNDED)
        summary.add_column("Version", style="cyan")
        summary.add_column("Removed Items", style="red")
        summary.add_column("Moved Items", style="blue")
        summary.add_column("Deprecated Items", style="yellow")
        summary.add_column("Screenshots", style="magenta")
        
        from_removed = len([i for i in from_result.get("items", []) if i.get("item_type") == "removed"])
        from_moved = len([i for i in from_result.get("items", []) if i.get("item_type") == "moved"])
        from_deprecated = len([i for i in from_result.get("items", []) if i.get("item_type") == "deprecated"])
        
        to_removed = len([i for i in to_result.get("items", []) if i.get("item_type") == "removed"])
        to_moved = len([i for i in to_result.get("items", []) if i.get("item_type") == "moved"])
        to_deprecated = len([i for i in to_result.get("items", []) if i.get("item_type") == "deprecated"])
        
        summary.add_row(
            from_version,
            str(from_removed),
            str(from_moved),
            str(from_deprecated),
            str(len(from_result.get("screenshots", [])))
        )
        summary.add_row(
            to_version,
            str(to_removed),
            str(to_moved),
            str(to_deprecated),
            str(len(to_result.get("screenshots", [])))
        )
        
        console.print(summary)
        console.print()
        
        # Show NEW removals in SP7 (not in SP6)
        if new_in_to:
            table = Table(title=f"🆕 NEW in {to_version} (not in {from_version})", box=box.ROUNDED, expand=True)
            table.add_column("Type", style="yellow", width=10)
            table.add_column("Package/Feature", style="cyan", width=25)
            table.add_column("Description", width=45)
            table.add_column("Replacement", style="green", width=12)
            
            for item in new_in_to:
                type_style = {"removed": "red", "moved": "blue", "deprecated": "yellow"}.get(item.get("item_type", ""), "white")
                table.add_row(
                    f"[{type_style}]{item.get('item_type', '').upper()}[/{type_style}]",
                    item.get("name", "")[:25],
                    item.get("description", "")[:45] + "..." if len(item.get("description", "")) > 45 else item.get("description", ""),
                    item.get("replacement") or "-"
                )
            
            console.print(table)
            console.print()
        
        # Show ALL items from TO version (SP7) 
        all_to_items = to_result.get("items", [])
        if all_to_items:
            # Removed
            removed = [i for i in all_to_items if i.get("item_type") == "removed"]
            if removed:
                table = Table(title=f"🗑️ All Removed in {to_version}", box=box.ROUNDED, expand=True)
                table.add_column("Package", style="red", width=22)
                table.add_column("Description", width=48)
                table.add_column("Replacement", style="green", width=12)
                
                for item in removed:
                    table.add_row(
                        item.get("name", "")[:22],
                        item.get("description", "")[:48] + "..." if len(item.get("description", "")) > 48 else item.get("description", ""),
                        item.get("replacement") or "-"
                    )
                console.print(table)
                console.print()
            
            # Moved
            moved = [i for i in all_to_items if i.get("item_type") == "moved"]
            if moved:
                table = Table(title=f"📦 All Moved in {to_version}", box=box.ROUNDED, expand=True)
                table.add_column("Package", style="blue", width=22)
                table.add_column("Description", width=48)
                table.add_column("Replacement", style="green", width=12)
                
                for item in moved:
                    table.add_row(
                        item.get("name", "")[:22],
                        item.get("description", "")[:48] + "..." if len(item.get("description", "")) > 48 else item.get("description", ""),
                        item.get("replacement") or "-"
                    )
                console.print(table)
                console.print()
            
            # Deprecated
            deprecated = [i for i in all_to_items if i.get("item_type") == "deprecated"]
            if deprecated:
                table = Table(title=f"⚠️ All Deprecated in {to_version}", box=box.ROUNDED, expand=True)
                table.add_column("Feature", style="yellow", width=25)
                table.add_column("Description", width=55)
                
                for item in deprecated:
                    table.add_row(
                        item.get("name", "")[:25],
                        item.get("description", "")[:55] + "..." if len(item.get("description", "")) > 55 else item.get("description", "")
                    )
                console.print(table)
        
        # Show screenshots
        all_screenshots = from_result.get("screenshots", []) + to_result.get("screenshots", [])
        if all_screenshots:
            console.print(f"\n[magenta]📸 Screenshots saved ({len(all_screenshots)}):[/magenta]")
            for ss in all_screenshots:
                console.print(f"   • {ss.get('section', 'page')}: [dim]{Path(ss.get('path', '')).name}[/dim]")
        
        # Save results
        output_dir = Path("./reports")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"precision_comparison_{timestamp}.json"
        
        final_result = {
            "from_version": from_version,
            "to_version": to_version,
            "from_url": from_url,
            "to_url": to_url,
            "from_items": from_result.get("items", []),
            "to_items": to_result.get("items", []),
            "new_in_to_version": new_in_to,
            "from_raw_sections": from_result.get("sections", {}),
            "to_raw_sections": to_result.get("sections", {}),
            "all_screenshots": all_screenshots,
            "timestamp": timestamp
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
        
        console.print(f"\n[green]💾 Results saved to:[/green] {output_file}\n")
        
        return final_result


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
