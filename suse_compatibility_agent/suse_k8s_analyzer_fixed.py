"""
SUSE Linux OS Compatibility Agent for Kubernetes
Fixed SSE parsing to match mino.ai API format
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


class SUSECompatibilityAnalyzer:
    """
    OS-Level Compatibility Agent
    Domain: SUSE Linux Enterprise Server
    Downstream Consumer: Kubernetes Agent
    """

    def __init__(self):
        self.api_key = os.getenv("MINO_API_KEY")
        if not self.api_key:
            raise ValueError("MINO_API_KEY not found")

        self.api_url = "https://mino.ai/v1/automation/run-sse"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }

    def analyze_os_upgrade(self, from_version: str, to_version: str, workload: str):
        """
        OS → Kubernetes compatibility analysis
        """

        goal = f"""Role: Senior Linux OS Compatibility Engineer (SUSE)

Agent Identity:
- Layer: Operating System
- Responsibility: Detect OS-level changes and predict downstream Kubernetes impact
- Output Consumer: Kubernetes Compatibility Agent

Task:
Analyze the OS upgrade from {from_version} to {to_version}.

Constraints:
- Focus ONLY on OS-level changes
- Do NOT propose Kubernetes architecture changes
- Do NOT include general release-note fluff

You must:
1. Identify breaking and behavioral OS changes
2. Explicitly map each change to Kubernetes components
3. Classify severity (CRITICAL/HIGH/MEDIUM/LOW)
4. Provide mitigations that can be executed by platform engineers

Return STRICT JSON using this schema:

{{
  "agent_metadata": {{
    "agent_name": "suse-os-agent",
    "domain": "operating-system",
    "confidence": 0.0,
    "evidence": ["list of documentation sources"]
  }},
  "upgrade": {{
    "from_version": "{from_version}",
    "to_version": "{to_version}",
    "workload": "{workload}"
  }},
  "breaking_changes": [
    {{
      "component": "component name",
      "change_type": "breaking|behavioral",
      "description": "technical description",
      "affected_k8s_components": ["kubelet", "container runtime", "networking"],
      "impact_severity": "CRITICAL|HIGH|MEDIUM|LOW"
    }}
  ],
  "kubernetes_impact": [
    {{
      "k8s_component": "component name",
      "impact_description": "impact explanation",
      "required_actions": ["actions"]
    }}
  ],
  "mitigation_steps": [
    {{
      "step": "number",
      "action": "action",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "timing": "pre-upgrade|during-upgrade|post-upgrade"
    }}
  ],
  "recommendations": ["recommendations"]
}}

If uncertain, state assumptions explicitly."""

        payload = {
            "url": "https://www.suse.com/releasenotes/",
            "goal": goal
        }

        print("\n🔄 Sending request to mino.ai...")
        
        with requests.post(
            self.api_url,
            headers=self.headers,
            json=payload,
            stream=True
        ) as response:
            response.raise_for_status()
            
            print("✓ Connected to API\n")
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    
                    # Parse the SSE event
                    try:
                        event = json.loads(decoded)
                        
                        event_type = event.get("type")
                        
                        if event_type == "STARTED":
                            print(f"🚀 Run started: {event.get('runId')}")
                        
                        elif event_type == "STREAMING_URL":
                            print(f"📺 Streaming URL: {event.get('streamingUrl')}")
                        
                        elif event_type == "PROGRESS":
                            print(f"  → {event.get('purpose', 'Processing...')}")
                        
                        elif event_type == "HEARTBEAT":
                            print("  💓 Heartbeat")
                        
                        elif event_type == "COMPLETE":
                            print("\n✅ Analysis complete!\n")
                            
                            # Extract the result
                            if "resultJson" in event:
                                result_json = event["resultJson"]
                                
                                # The result might be in a "result" field as a string
                                if "result" in result_json:
                                    raw_result = result_json["result"]
                                    
                                    # Remove markdown code fences if present
                                    if "```json" in raw_result:
                                        import re
                                        match = re.search(r'```json\s*(.*?)\s*```', raw_result, re.DOTALL)
                                        if match:
                                            raw_result = match.group(1).strip()
                                    elif "```" in raw_result:
                                        raw_result = raw_result.replace("```", "").strip()
                                    
                                    # Parse and return the JSON
                                    return json.loads(raw_result)
                                else:
                                    # Direct JSON object
                                    return result_json
                    
                    except json.JSONDecodeError:
                        # Not a JSON line, skip
                        continue
        
        # If we get here, no COMPLETE event was received
        return {
            "error": "No COMPLETE event received from API",
            "status": "failed"
        }

    def save(self, result: dict, file_name="os_analysis.json"):
        with open(file_name, "w") as f:
            json.dump(result, f, indent=2)


def main():
    """Execute SUSE 15 SP6 → SP7 compatibility analysis"""
    analyzer = SUSECompatibilityAnalyzer()
    
    print("=" * 80)
    print("SUSE OS Compatibility Analysis")
    print("Upgrade: SLES 15 SP6 → SLES 15 SP7")
    print("Target Workload: Kubernetes")
    print("=" * 80)
    
    result = analyzer.analyze_os_upgrade(
        from_version="SLES 15 SP6",
        to_version="SLES 15 SP7",
        workload="Kubernetes"
    )
    
    # Check if we got a valid result
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        if "status" in result:
            print(f"Status: {result['status']}")
    else:
        print("💾 Saving results...")
        analyzer.save(result, "suse15_sp6_to_sp7_analysis.json")
        print(f"✅ Saved to: suse15_sp6_to_sp7_analysis.json")
        
        # Display summary
        print(f"\n📊 Analysis Summary:")
        print(f"  • Breaking Changes: {len(result.get('breaking_changes', []))}")
        print(f"  • K8s Components Affected: {len(result.get('kubernetes_impact', []))}")
        print(f"  • Mitigation Steps: {len(result.get('mitigation_steps', []))}")
        print(f"  • Recommendations: {len(result.get('recommendations', []))}")
        
        if "agent_metadata" in result:
            print(f"\n🤖 Agent Metadata:")
            print(f"  • Confidence: {result['agent_metadata'].get('confidence', 'N/A')}")
            print(f"  • Evidence Sources: {len(result['agent_metadata'].get('evidence', []))}")


if __name__ == "__main__":
    main()
