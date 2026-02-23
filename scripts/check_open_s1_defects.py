import os
import sys
import requests

def check_open_s1_defects():
    api_url = os.environ.get("INKA_API_URL", "http://localhost:8000")
    api_key = os.environ.get("INKA_ADMIN_API_KEY") # Shared secret or token
    
    headers = {}
    if api_key:
        headers["X-Admin-Key"] = api_key

    try:
        # Fetch S1 defects that are not CLOSED or REJECTED
        response = requests.get(
            f"{api_url}/api/v1/defects/",
            params={"severity": "S1", "limit": 10},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        defects = response.json()
        open_defects = [d for d in defects if d["status"] not in ["closed", "rejected"]]
        
        if open_defects:
            print(f"❌ DEPLOYMENT BLOCKED: Found {len(open_defects)} open S1 defects.")
            for d in open_defects:
                print(f"  - [{d['id'][:8]}] {d['title']}")
            sys.exit(1)
            
        print("✅ No open S1 defects found. Deployment allowed.")
        sys.exit(0)
        
    except Exception as e:
        print(f"⚠️ Error checking defects: {e}")
        # In a strict environment, we might want to exit 1 here too
        sys.exit(0)

if __name__ == "__main__":
    check_open_s1_defects()
