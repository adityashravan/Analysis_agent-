"""
Utility to extract and clean JSON from raw SSE response
"""

import json
import re

def extract_json_from_sse(file_path):
    """Extract clean JSON from SSE response file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Try to find the raw_response field
    try:
        data = json.loads(content)
        if 'raw_response' in data:
            raw = data['raw_response']
        else:
            raw = content
    except:
        raw = content
    
    # Split by 'data: ' to get individual SSE events
    events = raw.split('data: ')
    
    result_json = None
    
    for event in events:
        if not event.strip():
            continue
            
        try:
            # Parse the event
            event_data = json.loads(event.split('data:')[0].strip())
            
            # Look for COMPLETE event with resultJson
            if event_data.get('type') == 'COMPLETE':
                if 'resultJson' in event_data and 'result' in event_data['resultJson']:
                    raw_result = event_data['resultJson']['result']
                    
                    # Remove markdown code fences
                    if '```json' in raw_result:
                        match = re.search(r'```json\s*(.*?)\s*```', raw_result, re.DOTALL)
                        if match:
                            raw_result = match.group(1).strip()
                    elif '```' in raw_result:
                        raw_result = raw_result.replace('```', '').strip()
                    
                    # Parse the final JSON
                    result_json = json.loads(raw_result)
                    break
        except json.JSONDecodeError:
            continue
    
    return result_json


if __name__ == "__main__":
    import sys
    
    input_file = "suse15_sp6_to_sp7_analysis.json"
    output_file = "suse15_sp6_to_sp7_CLEAN.json"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print(f"Extracting JSON from: {input_file}")
    
    result = extract_json_from_sse(input_file)
    
    if result:
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"✓ Cleaned JSON saved to: {output_file}")
        print(f"\n📊 Summary:")
        if "breaking_changes" in result:
            print(f"  - Breaking Changes: {len(result.get('breaking_changes', []))}")
        if "kubernetes_impact" in result:
            print(f"  - K8s Components: {len(result.get('kubernetes_impact', []))}")
        if "mitigation_steps" in result:
            print(f"  - Mitigation Steps: {len(result.get('mitigation_steps', []))}")
    else:
        print("✗ Could not extract JSON from file")
        print("\nTrying alternative extraction...")
        
        # Try to extract from earlier successful run
        try:
            with open("analysis_result.json", 'r') as f:
                old_content = f.read()
            
            old_result = extract_json_from_sse("analysis_result.json")
            if old_result:
                print("Found JSON in analysis_result.json")
                with open(output_file, 'w') as f:
                    json.dump(old_result, f, indent=2)
                print(f"✓ Saved to: {output_file}")
        except:
            print("No alternative source found")
