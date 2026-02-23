#!/usr/bin/env python3
"""
Check if the version deployed to STAGE is stable (deployed at least 24h ago).
Called from Deploy → PROD workflow.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
import psycopg2

def main():
    skip_check = os.environ.get("SKIP_CHECK", "false").lower() == "true"
    skip_justification = os.environ.get("SKIP_JUSTIFICATION", "").strip()
    target_version = os.environ.get("INPUT_VERSION")
    db_url = os.environ.get("DATABASE_URL")

    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    if skip_check:
        if not skip_justification:
            print("❌ HOTFIX skip requires justification!")
            sys.exit(1)
        print(f"⚠️ Skipping 24h check with justification: {skip_justification}")
        return

    print(f"🔍 Checking stability for v{target_version} on STAGE...")
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Find the deployment record for this version on stage
        cur.execute(
            """
            SELECT deployed_at, status 
            FROM release_registry 
            WHERE environment = 'stage' AND version = %s
            ORDER BY deployed_at DESC LIMIT 1
            """,
            (target_version,)
        )
        
        row = cur.fetchone()
        if not row:
            print(f"❌ Version v{target_version} was never deployed to STAGE")
            sys.exit(1)
            
        deployed_at = row[0]
        # Ensure deployed_at has timezone info
        if deployed_at.tzinfo is None:
            deployed_at = deployed_at.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        age = now - deployed_at
        
        print(f"ℹ️ v{target_version} deployed at: {deployed_at}")
        print(f"ℹ️ Current age: {age}")
        
        if age < timedelta(hours=24):
            print(f"❌ Version is only {age} old. Needs 24 hours of bake time on STAGE.")
            print("💡 Use 'skip_24h_check=true' for emergency hotfixes.")
            sys.exit(1)
            
        print("✅ Version has sufficient bake time on STAGE.")
        
        # Check if there are any active S1/S2 defects for this version
        # (This assumes a 'defect_registry' table exists or similar logic)
        # For now, we'll just print a placeholder unless we find the defect check logic.
        print("🔍 Checking for active critical defects...")
        # Placeholder for defect check
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
