import json
import os
import sys
import subprocess

# Setup paths
root = os.getcwd()
sys.path.insert(0, os.path.join(root, "apps/api/src"))

# Setup 'packages' symlinks if they don't exist (mimic Docker environment)
packages_dir = os.path.join(root, "packages")
if not os.path.exists(packages_dir):
    os.makedirs(packages_dir, exist_ok=True)
    with open(os.path.join(packages_dir, "__init__.py"), "w") as f:
        pass
    
    # List of libs to link
    libs = {
        "core": "packages.core",
        "db": "packages.db",
        "orchestrator": "packages.orchestrator"
    }
    
    for link_name, target_path in libs.items():
        link_path = os.path.join(packages_dir, link_name)
        if not os.path.exists(link_path):
            os.symlink(os.path.join(root, target_path), link_path)

sys.path.insert(0, root)

try:
    from app.main import app
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print(f"PYTHONPATH: {sys.path}")
    sys.exit(1)

def main():
    openapi_schema = app.openapi()
    output_path = "apps/api/openapi.json"
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"✅ OpenAPI schema generated at {output_path}")

    # Integrity Check
    paths = openapi_schema.get("paths", {})
    required_endpoints = ["/healthz", "/readyz", "/version"]
    missing = [ep for ep in required_endpoints if ep not in paths]
    
    if missing:
        print(f"❌ Missing mandatory endpoints: {missing}")
        sys.exit(1)
    
    print("✅ All mandatory endpoints present.")
    
    # Check version consistency
    version = openapi_schema.get("info", {}).get("version")
    print(f"✅ API Version: {version}")

if __name__ == "__main__":
    main()
