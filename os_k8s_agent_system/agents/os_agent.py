"""
OS Agent - SUSE Specialist (Mino-Inspired Architecture)
Analyzes OS version changes and their impacts using efficient LLM calls

Enhanced with upstream-downstream pattern:
- Accepts simple version strings from user
- Scrapes SUSE release notes using Playwright (Mino-style)
- Analyzes OS-level changes using scraped content
- Automatically propagates to downstream agents (Kubernetes, Database, etc.)
"""

import logging
import hashlib
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from core.models import (
    VersionChange, BreakingChange, MitigationStep,
    ImpactAnalysis, AgentMetadata, AnalysisReport
)
from core.knowledge_base import KnowledgeBaseManager
from core.base_agent import BaseAgent, AgentChange

logger = logging.getLogger(__name__)


class OSAgent(BaseAgent):
    """
    Senior Linux OS Compatibility Engineer (SUSE)
    
    Mino-Inspired Optimizations:
    - Web scraping first (Playwright) - fetch real data
    - Hierarchical prompting (reduce expensive LLM calls)
    - Response caching (avoid duplicate calls)
    - Goal-based extraction (structured output)
    - Streaming support for progress feedback
    
    Specializes in:
    - SUSE Linux Enterprise Server internals
    - Kernel and system-level changes
    - OS-level dependency management
    
    Upstream-Downstream Pattern:
    - Root agent in the dependency chain
    - Propagates OS changes to downstream agents automatically
    - Supports registering new downstream agents dynamically
    """
    
    # Response cache (Mino-style cost reduction)
    _cache: Dict[str, Any] = {}
    _cache_dir = Path("./cache")
    
    # SUSE Release Notes URLs - scraped for real data
    SUSE_RELEASE_NOTES_URLS = {
        "SLES 15 SP4": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP4/index.html",
        "SLES 15 SP5": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP5/index.html",
        "SLES 15 SP6": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP6/index.html",
        "SLES 15 SP7": "https://www.suse.com/releasenotes/x86_64/SUSE-SLES/15-SP7/index.html",
    }
    
    # Additional documentation sources to scrape
    SUSE_DOCS_URLS = [
        "https://documentation.suse.com/sles/15-SP7/html/SLES-all/cha-upgrade-background.html",
        "https://documentation.suse.com/sles/15-SP7/html/SLES-all/cha-upgrade-paths.html",
    ]
    
    def __init__(self, config, knowledge_base: KnowledgeBaseManager):
        # Initialize base agent
        super().__init__(config, knowledge_base, agent_name="os-agent", domain="operating-system")
        
        # Ensure cache directory exists
        self._cache_dir.mkdir(exist_ok=True)
        
        # Initialize LLM with streaming for progress feedback (Mino SSE-style)
        callbacks = [StreamingStdOutCallbackHandler()] if config.use_streaming else []
        
        if config.llm_provider == "openai":
            llm_kwargs = {
                "model": config.llm_model,
                "temperature": 0.1,
                "openai_api_key": config.openai_api_key,
                "max_retries": config.max_retries,
            }
            if hasattr(config, 'openai_base_url') and config.openai_base_url:
                llm_kwargs["base_url"] = config.openai_base_url
            self.llm = ChatOpenAI(**llm_kwargs)
        else:
            self.llm = ChatAnthropic(
                model=config.llm_model,
                temperature=0.1,
                anthropic_api_key=config.anthropic_api_key
            )
        
        # Mino-Style Goal-Based Prompt (The "Secret Sauce")
        # This is the key to good results - structured task specification
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Linux OS Compatibility Engineer specializing in SUSE Linux Enterprise Server.

=== AGENT IDENTITY (Mino-Style) ===
Layer: Operating System
Responsibility: Detect OS-level changes and predict downstream Kubernetes impact
Output Consumer: Kubernetes Compatibility Agent

=== YOUR EXPERTISE ===
- SUSE Linux Enterprise Server internals and release notes
- Kernel version changes, driver updates, and system impacts
- System library and package management (zypper, RPM)
- cgroups v1/v2 transitions and container impacts
- Container runtime compatibility (CRI-O, containerd, podman)
- systemd, networking (DHCP, DNS), and init system changes

=== CONSTRAINTS ===
- Focus ONLY on OS-level changes
- Be EXTREMELY SPECIFIC - name exact packages, config files, drivers
- Cite specific sources and documentation URLs
- State impact severity honestly (CRITICAL/HIGH/MEDIUM/LOW)
- Do NOT propose Kubernetes architecture changes
- Do NOT include general release-note fluff"""),
            
            ("human", """=== TASK ===
Analyze the upgrade from {from_version} to {to_version} for Kubernetes workloads.

=== CONTEXT FROM KNOWLEDGE BASE ===
{context}

=== REQUIRED OUTPUT ===
Return a valid JSON object with this EXACT structure:

{{
  "breaking_changes": [
    {{
      "component": "Exact component name (e.g., 'Container Runtime Configuration', 'Kernel Driver Stability (smc)')",
      "change_type": "breaking|behavioral|deprecated",
      "description": "Detailed technical description. Include specific file paths, package names, configuration keys. Explain WHY this breaks existing functionality.",
      "impact_severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "affected_k8s_components": ["kubelet", "container runtime", "specific affected components"]
    }}
  ],
  "evidence_sources": [
    "https://www.suse.com/releasenotes/...",
    "Other documentation URLs"
  ],
  "mitigation_steps": [
    {{
      "step": "1",
      "action": "SPECIFIC action with exact commands, file paths, configuration changes. Example: 'Deploy configuration to pre-populate /etc/containers/registries.conf with explicit Docker Hub registry'",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "timing": "pre-upgrade|during-upgrade|post-upgrade"
    }}
  ],
  "recommendations": [
    "Specific strategic recommendations with business context"
  ]
}}

=== FOCUS AREAS ===
1. Removed or deprecated packages (like redis, dhcpd)
2. Kernel driver changes or known issues
3. Container registry configuration changes
4. System library version changes (glibc, systemd)
5. Networking stack changes (DHCP, DNS, time sync)
6. Security/authentication changes

=== OUTPUT RULES ===
- Name the EXACT component (package name, driver name, config file)
- Describe WHAT changed technically
- State WHY it breaks existing setups
- Specify affected K8s components
- Provide actionable mitigation with specific commands/paths
- Output ONLY the JSON object, no markdown, no explanations.""")
        ])
        
        self.impact_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are analyzing the downstream impact of OS changes on {target_layer}.
Map each OS-level change to specific impacts on the target layer."""),
            
            ("human", """OS Changes:
{os_changes}

Target Layer: {target_layer}
Context:
{context}

For each OS change, determine:
1. Which {target_layer} components are affected
2. How they are affected (specific behavior changes)
3. What actions are required to mitigate
4. Risk level of not taking action

Be specific about component names, configuration files, and required changes.""")
        ])
    
    def _get_cache_key(self, version_change: VersionChange) -> str:
        """Generate cache key for version change analysis"""
        key_str = f"{version_change.from_version}:{version_change.to_version}:{version_change.workload}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Load cached analysis result (Mino-style cost reduction)"""
        if not self.config.enable_caching:
            return None
        
        cache_file = self._cache_dir / f"os_analysis_{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    logger.info(f"📦 Loading cached analysis: {cache_key[:8]}...")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Cache load failed: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Save analysis result to cache"""
        if not self.config.enable_caching:
            return
            
        cache_file = self._cache_dir / f"os_analysis_{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"💾 Cached analysis: {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    # ============================================
    # WEB SCRAPING METHODS (Mino-Style) with Screenshots
    # ============================================
    
    # Screenshots directory
    _screenshots_dir = Path("./screenshots")
    
    def _get_release_notes_url(self, version: str) -> str:
        """Get URL for a SUSE version's release notes"""
        if version in self.SUSE_RELEASE_NOTES_URLS:
            return self.SUSE_RELEASE_NOTES_URLS[version]
        
        # Try to construct URL from version string
        # e.g., "SLES 15 SP7" -> "15-SP7"
        version_clean = version.replace("SLES ", "").replace(" ", "-")
        return f"https://www.suse.com/releasenotes/x86_64/SUSE-SLES/{version_clean}/index.html"
    
    async def _scrape_release_notes_async(self, version: str) -> Dict[str, Any]:
        """Scrape release notes using Playwright (async) with screenshots for verification"""
        from datetime import datetime
        
        url = self._get_release_notes_url(version)
        print(f"   🌐 Scraping: {url}", flush=True)
        
        # Ensure screenshots directory exists
        self._screenshots_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_safe = version.replace(" ", "_").replace(".", "-")
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not installed. Run: uv pip install playwright && playwright install chromium")
            return {"error": "Playwright not installed", "url": url, "version": version}
        
        scraped_data = {
            "url": url,
            "version": version,
            "removed_deprecated": "",
            "technology_changes": "",
            "known_issues": "",
            "full_content": "",
            "scrape_success": False,
            "screenshots": [],
            "sections_found": [],
            "scrape_timestamp": timestamp
        }
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1920, "height": 1080})
                
                print(f"   📄 Loading page...", flush=True)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for dynamic content
                
                # Screenshot 1: Full page after load
                screenshot_path = self._screenshots_dir / f"{version_safe}_{timestamp}_01_full_page.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                scraped_data["screenshots"].append({
                    "name": "Full Page",
                    "path": str(screenshot_path),
                    "description": f"Complete page view of {version} release notes"
                })
                print(f"   📸 Screenshot saved: {screenshot_path.name}", flush=True)
                
                # Extract specific sections
                print(f"   🔍 Extracting sections...", flush=True)
                
                # Get the full content first
                full_text = await page.inner_text("body")
                scraped_data["full_content"] = full_text[:50000]  # Limit size
                
                # Try to find removed/deprecated section
                removed_sections = await page.query_selector_all("[id*='removed'], [id*='deprecated'], [id*='Removed'], [id*='Deprecated']")
                if removed_sections:
                    texts = []
                    for i, section in enumerate(removed_sections[:3]):
                        # Scroll to section and screenshot
                        await section.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        
                        # Take screenshot of this section
                        screenshot_path = self._screenshots_dir / f"{version_safe}_{timestamp}_02_removed_{i+1}.png"
                        await page.screenshot(path=str(screenshot_path))
                        scraped_data["screenshots"].append({
                            "name": f"Removed/Deprecated Section {i+1}",
                            "path": str(screenshot_path),
                            "description": "Section showing removed or deprecated features"
                        })
                        print(f"   📸 Screenshot saved: {screenshot_path.name}", flush=True)
                        
                        parent = await section.evaluate_handle("el => el.closest('section') || el.parentElement || el")
                        text = await parent.inner_text()
                        texts.append(text)
                    scraped_data["removed_deprecated"] = "\n\n".join(texts)
                    scraped_data["sections_found"].append({
                        "section": "Removed/Deprecated",
                        "count": len(removed_sections),
                        "chars_extracted": len(scraped_data["removed_deprecated"])
                    })
                
                # Try to find technology changes
                tech_sections = await page.query_selector_all("[id*='technology'], [id*='Technology'], [id*='changes'], [id*='Changes']")
                if tech_sections:
                    texts = []
                    for i, section in enumerate(tech_sections[:2]):
                        await section.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        
                        screenshot_path = self._screenshots_dir / f"{version_safe}_{timestamp}_03_tech_{i+1}.png"
                        await page.screenshot(path=str(screenshot_path))
                        scraped_data["screenshots"].append({
                            "name": f"Technology Changes Section {i+1}",
                            "path": str(screenshot_path),
                            "description": "Section showing technology and system changes"
                        })
                        print(f"   📸 Screenshot saved: {screenshot_path.name}", flush=True)
                        
                        parent = await section.evaluate_handle("el => el.closest('section') || el.parentElement || el")
                        text = await parent.inner_text()
                        texts.append(text)
                    scraped_data["technology_changes"] = "\n\n".join(texts)
                    scraped_data["sections_found"].append({
                        "section": "Technology Changes",
                        "count": len(tech_sections),
                        "chars_extracted": len(scraped_data["technology_changes"])
                    })
                
                # Try to find known issues
                issues_sections = await page.query_selector_all("[id*='known'], [id*='Known'], [id*='issues'], [id*='Issues']")
                if issues_sections:
                    texts = []
                    for i, section in enumerate(issues_sections[:2]):
                        await section.scroll_into_view_if_needed()
                        await page.wait_for_timeout(500)
                        
                        screenshot_path = self._screenshots_dir / f"{version_safe}_{timestamp}_04_issues_{i+1}.png"
                        await page.screenshot(path=str(screenshot_path))
                        scraped_data["screenshots"].append({
                            "name": f"Known Issues Section {i+1}",
                            "path": str(screenshot_path),
                            "description": "Section showing known issues and bugs"
                        })
                        print(f"   📸 Screenshot saved: {screenshot_path.name}", flush=True)
                        
                        parent = await section.evaluate_handle("el => el.closest('section') || el.parentElement || el")
                        text = await parent.inner_text()
                        texts.append(text)
                    scraped_data["known_issues"] = "\n\n".join(texts)
                    scraped_data["sections_found"].append({
                        "section": "Known Issues",
                        "count": len(issues_sections),
                        "chars_extracted": len(scraped_data["known_issues"])
                    })
                
                scraped_data["scrape_success"] = True
                await browser.close()
                
                # Print summary
                print(f"   ✅ Scraped {len(scraped_data['full_content'])} chars from {version}", flush=True)
                print(f"   📸 Total screenshots: {len(scraped_data['screenshots'])}", flush=True)
                print(f"   📋 Sections found: {len(scraped_data['sections_found'])}", flush=True)
                
        except Exception as e:
            logger.error(f"Scraping failed for {version}: {e}")
            scraped_data["error"] = str(e)
        
        return scraped_data
    
    def _scrape_release_notes(self, version: str) -> Dict[str, Any]:
        """Synchronous wrapper for scraping"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._scrape_release_notes_async(version))
    
    def _scrape_multiple_versions(self, from_version: str, to_version: str) -> Dict[str, Any]:
        """Scrape release notes for both versions and combine - returns context and metadata"""
        print("\n" + "="*70, flush=True)
        print("  🌐 WEB SCRAPING: Fetching REAL SUSE Release Notes", flush=True)
        print("="*70, flush=True)
        
        # Scrape target version (most important)
        print(f"\n📥 Fetching {to_version} release notes...", flush=True)
        to_notes = self._scrape_release_notes(to_version)
        
        # Scrape source version for comparison
        print(f"\n📥 Fetching {from_version} release notes...", flush=True)
        from_notes = self._scrape_release_notes(from_version)
        
        # Combine scraped content into context
        context_parts = []
        all_screenshots = []
        all_sections = []
        source_urls = []
        
        if to_notes.get("scrape_success"):
            context_parts.append(f"""
=== {to_version} RELEASE NOTES (TARGET VERSION) ===
URL: {to_notes.get('url')}

--- REMOVED AND DEPRECATED FEATURES ---
{to_notes.get('removed_deprecated', 'Section not found')[:15000]}

--- TECHNOLOGY CHANGES ---
{to_notes.get('technology_changes', 'Section not found')[:5000]}

--- KNOWN ISSUES ---
{to_notes.get('known_issues', 'Section not found')[:5000]}
""")
            all_screenshots.extend(to_notes.get("screenshots", []))
            all_sections.extend(to_notes.get("sections_found", []))
            source_urls.append(to_notes.get("url"))
        else:
            context_parts.append(f"⚠️ Failed to scrape {to_version}: {to_notes.get('error', 'Unknown error')}")
        
        if from_notes.get("scrape_success"):
            context_parts.append(f"""
=== {from_version} RELEASE NOTES (SOURCE VERSION) ===
URL: {from_notes.get('url')}

--- KEY CONTENT (for comparison) ---
{from_notes.get('full_content', '')[:10000]}
""")
            all_screenshots.extend(from_notes.get("screenshots", []))
            all_sections.extend(from_notes.get("sections_found", []))
            source_urls.append(from_notes.get("url"))
        
        combined = "\n\n".join(context_parts)
        print(f"\n✅ Combined scraped content: {len(combined)} characters", flush=True)
        print(f"📸 Total screenshots captured: {len(all_screenshots)}", flush=True)
        print("="*70 + "\n", flush=True)
        
        # Return both context and metadata
        return {
            "context": combined,
            "screenshots": all_screenshots,
            "sections_found": all_sections,
            "source_urls": source_urls,
            "from_notes_success": from_notes.get("scrape_success", False),
            "to_notes_success": to_notes.get("scrape_success", False),
            "scrape_timestamp": to_notes.get("scrape_timestamp", "")
        }
    
    def analyze_version_change(self, version_change: VersionChange) -> Dict[str, Any]:
        """
        Analyze OS version change (Mino-Inspired)
        
        Flow:
        1. Check cache first (avoid duplicate work)
        2. SCRAPE real SUSE release notes using Playwright
        3. Use scraped content as LLM context
        4. Single consolidated LLM call for analysis
        """
        logger.info(f"OS Agent analyzing: {version_change.from_version} → {version_change.to_version}")
        
        # Check cache first (Mino 90% cost reduction principle)
        cache_key = self._get_cache_key(version_change)
        cached = self._load_from_cache(cache_key)
        if cached:
            logger.info("✅ Using cached analysis (saved LLM cost!)")
            return cached
        
        # STEP 1: Scrape SUSE release notes (Mino-style web automation)
        print("   📡 Step 1: Scraping SUSE release notes (Playwright)...", flush=True)
        scrape_result = self._scrape_multiple_versions(
            version_change.from_version, 
            version_change.to_version
        )
        
        # Extract context and metadata from scrape result
        scraped_context = scrape_result.get("context", "")
        scrape_metadata = {
            "screenshots": scrape_result.get("screenshots", []),
            "sections_found": scrape_result.get("sections_found", []),
            "source_urls": scrape_result.get("source_urls", []),
            "scrape_timestamp": scrape_result.get("scrape_timestamp", "")
        }
        
        # STEP 2: Also get knowledge base context (if available)
        print("   📚 Step 2: Checking local knowledge base...", flush=True)
        query = f"""
        {version_change.from_version} {version_change.to_version} release notes
        breaking changes deprecated removed packages
        kernel changes driver issues systemd networking container runtime
        """
        kb_context = self.kb.get_relevant_context(query, max_tokens=4000)
        
        # STEP 3: Combine contexts - scraped data is PRIMARY
        if scraped_context and len(scraped_context.strip()) > 500:
            context = scraped_context
            if kb_context and len(kb_context.strip()) > 100:
                context += f"\n\n=== ADDITIONAL KNOWLEDGE BASE CONTEXT ===\n{kb_context}"
            print(f"   ✅ Using SCRAPED content as primary source ({len(context)} chars)", flush=True)
        elif kb_context and len(kb_context.strip()) > 100:
            context = kb_context
            print("   ⚠️ Scraping failed, using knowledge base only", flush=True)
        else:
            context = "No scraped or knowledge base context available. Use your training knowledge of SUSE Enterprise Linux."
            print("   ⚠️ No external context available, using LLM knowledge only", flush=True)
        
        # STEP 4: Run LLM analysis with scraped context
        print("   🧠 Step 3: Running LLM analysis on scraped content...", flush=True)
        chain = self.analysis_prompt | self.llm
        result = chain.invoke({
            "from_version": version_change.from_version,
            "to_version": version_change.to_version,
            "context": context
        })
        
        # Parse JSON response
        import re
        
        content = result.content.strip()
        # Extract JSON if wrapped in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1)
        
        try:
            analysis_data = json.loads(content)
            logger.info(f"OS Agent analysis complete: {len(analysis_data.get('breaking_changes', []))} breaking changes found")
            
            # Add scrape metadata to analysis_data for verification
            analysis_data["scrape_verification"] = scrape_metadata
            
            # Cache successful result
            self._save_to_cache(cache_key, analysis_data)
            
            return analysis_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {content[:500]}")
            # Return minimal structure with scrape metadata
            return {
                "breaking_changes": [],
                "evidence_sources": [],
                "mitigation_steps": [],
                "recommendations": [],
                "parse_error": str(e),
                "raw_response": content,
                "scrape_verification": scrape_metadata
            }
    
    def analyze_impact(self, os_changes: str, target_layer: str) -> str:
        """
        Analyze impact of OS changes on target layer
        """
        query = f"{target_layer} compatibility {os_changes}"
        context = self.kb.get_relevant_context(query, max_tokens=4000)
        
        chain = self.impact_prompt | self.llm
        result = chain.invoke({
            "os_changes": os_changes,
            "target_layer": target_layer,
            "context": context
        })
        
        return result.content
    
    def get_metadata(self) -> AgentMetadata:
        """Get agent metadata"""
        return AgentMetadata(
            agent_name="suse-os-agent",
            domain="operating-system",
            confidence=0.0,  # Will be calculated based on evidence
            evidence_sources=[]
        )

    
    # BaseAgent abstract methods implementation
    
    def analyze_changes(self, from_version: str, to_version: str, **kwargs) -> Dict[str, Any]:
        """
        Simplified interface - user just provides two version strings
        
        Args:
            from_version: Source OS version (e.g., "SLES 15 SP6")
            to_version: Target OS version (e.g., "SLES 15 SP7")
            
        Returns:
            Structured analysis with changes, impacts, and recommendations
        """
        logger.info(f"OS Agent: Analyzing {from_version} → {to_version}")
        
        # Create version change object internally
        version_change = VersionChange(
            layer="OS",
            from_version=from_version,
            to_version=to_version,
            workload=kwargs.get('workload', 'Kubernetes')
        )
        
        # Run existing analysis
        os_analysis = self.analyze_version_change(version_change)
        
        # Convert to standard change format
        changes = []
        for breaking_change in os_analysis.get('breaking_changes', []):
            changes.append(AgentChange(
                component=breaking_change.get('component', 'Unknown'),
                change_type=breaking_change.get('change_type', 'unknown'),
                description=breaking_change.get('description', ''),
                severity=breaking_change.get('impact_severity', 'MEDIUM'),
                metadata={
                    'affected_k8s_components': breaking_change.get('affected_k8s_components', []),
                    'source': 'os-agent'
                }
            ))
        
        result = {
            'changes': changes,
            'metadata': {
                'agent_name': self.agent_name,
                'domain': self.domain,
                'from_version': from_version,
                'to_version': to_version,
                'evidence_sources': os_analysis.get('evidence_sources', [])
            },
            'mitigation_steps': os_analysis.get('mitigation_steps', []),
            'recommendations': os_analysis.get('recommendations', []),
            'raw_analysis': os_analysis,  # Keep full analysis for reference
            'scrape_verification': os_analysis.get('scrape_verification', {})  # Screenshots and source tracking
        }
        
        # Auto-propagate to downstream agents
        if self._downstream_agents:
            logger.info(f"OS Agent: Propagating {len(changes)} changes to downstream agents...")
            downstream_results = self.propagate_to_downstream(changes)
            result['downstream_impacts'] = downstream_results
        
        return result
    
    def analyze_upstream_impact(self, upstream_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        OS Agent is typically a root agent, so this may not be called often
        But we implement it for flexibility (e.g., if firmware/BIOS changes affect OS)
        """
        logger.info(f"OS Agent: Analyzing {len(upstream_changes)} upstream changes")
        
        # For now, log and pass through
        # Could analyze how hardware/firmware changes affect OS in future
        return {
            'impacts': [],
            'required_actions': [],
            'risk_level': 'LOW',
            'note': 'OS Agent typically does not have upstream dependencies'
        }