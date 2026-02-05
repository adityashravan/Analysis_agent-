"""
Browser Agent - Mino-Style Web Automation
Actually navigates to websites, extracts content, and uses LLM for analysis
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TaskStep:
    """Represents a step in the task execution"""
    name: str
    status: str = "pending"  # pending, running, completed, failed
    duration: float = 0.0
    result: Any = None


class ProgressTracker:
    """SSE-style progress tracking like Mino"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.steps: List[TaskStep] = []
        self.callback = callback or self._default_callback
        self.start_time = time.time()
    
    def _default_callback(self, event_type: str, data: Dict):
        """Default progress display"""
        if event_type == "STARTED":
            print(f"\n🚀 Task Started: {data.get('goal', '')[:60]}...")
        elif event_type == "STEP_START":
            print(f"   ⏳ {data.get('step_name', '')}...", end="", flush=True)
        elif event_type == "STEP_COMPLETE":
            print(f" ✅ ({data.get('duration', 0):.1f}s)")
        elif event_type == "PROGRESS":
            print(f"   📊 Progress: {data.get('progress', 0)}%")
        elif event_type == "COMPLETE":
            print(f"\n✅ Task Completed in {data.get('total_time', 0):.1f}s")
    
    def start_task(self, goal: str):
        self.start_time = time.time()
        self.callback("STARTED", {"goal": goal, "timestamp": datetime.now().isoformat()})
    
    def start_step(self, name: str):
        step = TaskStep(name=name, status="running")
        step.start_time = time.time()
        self.steps.append(step)
        self.callback("STEP_START", {"step_name": name})
    
    def complete_step(self, result: Any = None):
        if self.steps:
            step = self.steps[-1]
            step.status = "completed"
            step.duration = time.time() - step.start_time
            step.result = result
            self.callback("STEP_COMPLETE", {
                "step_name": step.name, 
                "duration": step.duration
            })
    
    def complete_task(self):
        total_time = time.time() - self.start_time
        self.callback("COMPLETE", {"total_time": total_time})


class BrowserAgent:
    """
    Mino-Style Browser Automation Agent
    
    Actually does what Mino does:
    1. Navigates to real URLs
    2. Extracts page content (DOM, text, screenshots)
    3. Uses LLM to analyze extracted content
    4. Returns structured data
    """
    
    def __init__(self, config):
        self.config = config
        self.browser = None
        self.page = None
        self.progress = ProgressTracker()
        
    async def _ensure_browser(self):
        """Lazy-load browser on first use"""
        if self.browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self.browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                self.page = await self.browser.new_page()
                logger.info("Browser initialized")
            except ImportError:
                logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
                raise
    
    async def navigate(self, url: str, wait_for: str = "networkidle") -> str:
        """Navigate to URL and return page content"""
        await self._ensure_browser()
        
        self.progress.start_step(f"Navigate to {url[:50]}...")
        
        try:
            await self.page.goto(url, wait_until=wait_for, timeout=30000)
            await self.page.wait_for_load_state("domcontentloaded")
            
            # Get page content
            content = await self.page.content()
            self.progress.complete_step()
            return content
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            self.progress.complete_step()
            return ""
    
    async def extract_text(self, selector: str = "body") -> str:
        """Extract text content from page"""
        self.progress.start_step("Extract page text content")
        
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.inner_text()
                self.progress.complete_step()
                return text
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
        
        self.progress.complete_step()
        return ""
    
    async def take_screenshot(self, path: str = None) -> bytes:
        """Take screenshot of current page"""
        self.progress.start_step("Capture page screenshot")
        
        try:
            screenshot = await self.page.screenshot(full_page=False)
            if path:
                with open(path, 'wb') as f:
                    f.write(screenshot)
            self.progress.complete_step()
            return screenshot
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            self.progress.complete_step()
            return b""
    
    async def extract_structured_data(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract structured data using CSS selectors"""
        self.progress.start_step("Extract structured data")
        
        data = {}
        for key, selector in selectors.items():
            try:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    texts = [await el.inner_text() for el in elements]
                    data[key] = texts if len(texts) > 1 else texts[0] if texts else None
            except Exception as e:
                logger.warning(f"Failed to extract {key}: {e}")
                data[key] = None
        
        self.progress.complete_step()
        return data
    
    async def click_and_wait(self, selector: str):
        """Click element and wait for navigation"""
        self.progress.start_step(f"Click: {selector[:30]}...")
        
        try:
            await self.page.click(selector)
            await self.page.wait_for_load_state("networkidle")
            self.progress.complete_step()
            return True
        except Exception as e:
            logger.error(f"Click failed: {e}")
            self.progress.complete_step()
            return False
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            await self._playwright.stop()
            self.browser = None
            self.page = None


class SUSEReleaseNotesAgent:
    """
    Specialized agent for SUSE release notes extraction
    Mimics Mino's workflow: Navigate → Extract → Analyze
    """
    
    # Known SUSE release notes URLs - use index.html for full content
    SUSE_URLS = {
        "SLES 15 SP6": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP6/index.html",
        "SLES 15 SP7": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP7/index.html",
    }
    
    def __init__(self, config, llm):
        self.config = config
        self.llm = llm
        self.browser_agent = BrowserAgent(config)
    
    async def fetch_release_notes(self, version: str) -> Dict[str, Any]:
        """Fetch and extract release notes for a SUSE version"""
        
        url = self.SUSE_URLS.get(version)
        if not url:
            # Try to construct URL
            url = f"https://www.suse.com/releasenotes/x86_64/SUSE-SLES/{version.replace('SLES ', '').replace(' ', '-')}/index.html"
        
        print(f"\n📡 Fetching release notes from: {url}")
        self.browser_agent.progress.start_task(f"Fetch {version} release notes")
        
        try:
            # Navigate to the page
            await self.browser_agent.navigate(url)
            
            # Extract SPECIFIC sections we care about
            # Section 9: Removed and deprecated features
            removed_content = await self._extract_section(
                "#removed, #cha-removed, [id*='removed'], [id*='deprecated']",
                "Removed/Deprecated section"
            )
            
            # Section for technology changes
            tech_changes = await self._extract_section(
                "#technology, #cha-technology, [id*='technology']",
                "Technology changes"
            )
            
            # Section for known issues
            known_issues = await self._extract_section(
                "#known-issues, #cha-known-issues, [id*='known']",
                "Known issues"
            )
            
            # Also get the full body as fallback
            full_content = await self.browser_agent.extract_text("article, main, .content, body")
            
            self.browser_agent.progress.complete_task()
            
            return {
                "url": url,
                "version": version,
                "removed_deprecated": removed_content,
                "technology_changes": tech_changes,
                "known_issues": known_issues,
                "full_content": full_content[:30000],
                "fetch_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch release notes: {e}")
            return {"error": str(e), "version": version}
        finally:
            await self.browser_agent.close()
    
    async def _extract_section(self, selector: str, section_name: str) -> str:
        """Extract a specific section from the page"""
        self.browser_agent.progress.start_step(f"Extract: {section_name}")
        
        try:
            # Try to find the section
            elements = await self.browser_agent.page.query_selector_all(selector)
            
            if elements:
                texts = []
                for el in elements:
                    # Get the parent section or the element itself
                    parent = await el.evaluate_handle("el => el.closest('section') || el.parentElement || el")
                    text = await parent.inner_text()
                    texts.append(text)
                
                content = "\n\n".join(texts)
                self.browser_agent.progress.complete_step()
                return content
            
            # Fallback: search by heading text
            headings = await self.browser_agent.page.query_selector_all("h1, h2, h3")
            for heading in headings:
                text = await heading.inner_text()
                if "removed" in text.lower() or "deprecated" in text.lower():
                    # Get the section content
                    section_content = await heading.evaluate_handle("""
                        el => {
                            let content = el.textContent + '\\n';
                            let next = el.nextElementSibling;
                            while (next && !['H1', 'H2'].includes(next.tagName)) {
                                content += next.textContent + '\\n';
                                next = next.nextElementSibling;
                            }
                            return content;
                        }
                    """)
                    content = await section_content.json_value()
                    self.browser_agent.progress.complete_step()
                    return content
                    
        except Exception as e:
            logger.warning(f"Failed to extract {section_name}: {e}")
        
        self.browser_agent.progress.complete_step()
        return ""
    
    async def analyze_upgrade(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """
        Complete Mino-style workflow:
        1. Fetch release notes for both versions
        2. Extract relevant content (specifically removed/deprecated sections)
        3. Use LLM to analyze differences
        """
        
        print("\n" + "="*70)
        print("  MINO-STYLE WEB AGENT: SUSE Upgrade Analysis")
        print("="*70)
        
        # Step 1: Fetch release notes
        print(f"\n📥 Step 1: Fetching release notes...")
        
        from_notes = await self.fetch_release_notes(from_version)
        to_notes = await self.fetch_release_notes(to_version)
        
        # Step 2: Prepare content for LLM analysis
        # Focus on the SPECIFIC sections about removed/deprecated features
        print(f"\n🧠 Step 2: Analyzing with LLM...")
        
        # Build focused content from the target version (SP7)
        target_removed = to_notes.get('removed_deprecated', '')
        target_tech = to_notes.get('technology_changes', '')
        target_issues = to_notes.get('known_issues', '')
        
        # If specific sections weren't found, use full content
        if not target_removed:
            print("   ⚠️  Specific sections not found, using full content...")
            target_removed = to_notes.get('full_content', '')[:20000]
        
        combined_content = f"""
=== {to_version} REMOVED AND DEPRECATED FEATURES ===
{target_removed[:15000]}

=== {to_version} TECHNOLOGY CHANGES ===
{target_tech[:5000]}

=== {to_version} KNOWN ISSUES ===
{target_issues[:5000]}

=== {from_version} CONTEXT (for comparison) ===
{from_notes.get('removed_deprecated', from_notes.get('full_content', ''))[:8000]}
"""
        
        print(f"   📄 Extracted content length: {len(combined_content)} chars")
        
        # Step 3: LLM Analysis
        analysis = await self._llm_analyze(from_version, to_version, combined_content)
        
        return {
            "from_version": from_version,
            "to_version": to_version,
            "source_data": {
                "from_url": from_notes.get("url"),
                "to_url": to_notes.get("url"),
            },
            "analysis": analysis
        }
    
    async def _llm_analyze(self, from_ver: str, to_ver: str, content: str) -> Dict[str, Any]:
        """Use LLM to analyze the extracted content"""
        from langchain_core.prompts import ChatPromptTemplate
        
        # NOTE: Double curly braces {{ }} escape them in LangChain templates
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a SUSE Linux compatibility expert. Your job is to ACCURATELY extract information from the release notes content provided.

CRITICAL RULES:
1. ONLY report what is EXPLICITLY stated in the content
2. DO NOT hallucinate or make up information
3. If something is mentioned as "reintroduced" or "available", it is NOT removed
4. Quote exact package names and versions from the content
5. Include the recommended replacement if mentioned (e.g., "use valkey instead of redis")

OUTPUT FORMAT: Return ONLY valid JSON:
{{
  "breaking_changes": [
    {{
      "component": "exact package name from content",
      "change_type": "removed|deprecated|moved",
      "description": "exact description from release notes",
      "replacement": "replacement package if mentioned, or null",
      "impact_severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "affected_k8s_components": ["kubelet", "container-runtime", etc] 
    }}
  ],
  "mitigation_steps": [
    {{
      "step": "1",
      "action": "specific action based on release notes",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "timing": "pre-upgrade|during-upgrade|post-upgrade"
    }}
  ],
  "evidence_sources": ["URLs mentioned in content"],
  "recommendations": ["actionable recommendations based on content"]
}}"""),
            ("human", """Analyze the upgrade from {from_version} to {to_version}.

EXTRACTED RELEASE NOTES CONTENT (this is the SOURCE OF TRUTH):
{content}

EXTRACT ONLY what is in the content above. Look for:
1. Packages marked as "removed" - list each one with its replacement
2. Packages marked as "deprecated" - note they will be removed later
3. Packages "moved to Package Hub" or "moved to Legacy Module"
4. Features disabled or changed
5. Any mentioned K8s/container impacts

DO NOT make up information. If a package is "reintroduced" it is NOT removed.

Return ONLY JSON with accurate information from the content.""")
        ])
        
        chain = prompt | self.llm
        
        try:
            result = chain.invoke({
                "from_version": from_ver,
                "to_version": to_ver,
                "content": content
            })
            
            # Parse JSON from response
            import re
            response_text = result.content.strip()
            
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return json.loads(response_text)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {"error": "Failed to parse LLM response", "raw": result.content[:500]}
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"error": str(e)}


# Synchronous wrapper for easier use
def run_async(coro):
    """Run async function synchronously"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
