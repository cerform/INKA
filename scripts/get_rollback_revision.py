#!/usr/bin/env python3
"""
Find the previous stable revision for rollback.
Outputs GITHUB_OUTPUT variables for the rollback workflow.
"""
import os
import sys
import psycopg2

def main():
    db_url = os.environ.get("DATABASE_URL")
    environment = os.environ.get("ENVIRONMENT")

    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Get the latest DEPLOYED or SUPERSEDED revision that is NOT the current failed one
        # Actually, we just want the latest one with status 'SUPERSEDED' 
        # because the current one is 'DEPLOYED'.
        cur.execute(
            """
            SELECT rollback_revision, version 
            FROM release_registry 
            WHERE environment = %s AND status = 'SUPERSEDED'
            ORDER BY deployed_at DESC LIMIT 1
            """,
            (environment,)
        )
        
        row = cur.fetchone()
        if not row:
            print(f"❌ No previous stable revision found exactly for environment: {environment}")
            # Fallback: just get the 2nd latest record
            cur.execute(
                """
                SELECT rollback_revision, version 
                FROM release_registry 
                WHERE environment = %s
                ORDER BY deployed_at DESC OFFSET 1 LIMIT 1
                """,
                (environment,)
            )
            row = cur.fetchone()

        if not row or not row[0]:
            print(f"❌ Could not find a valid rollback revision in registry for {environment}")
            sys.exit(1)
            
        rollback_rev = row[0]
        version = row[1]
        
        print(f"✅ Found rollback revision: {rollback_rev} (v{version})")
        
        # In GitHub Actions, we write to GITHUB_OUTPUT
        output_file = os.environ.get("GITHUB_OUTPUT")
        if output_file:
            with open(output_file, "a") as f:
                f.write(f"rollback_revision={rollback_rev}\n")
                # Also assume bot revision might be tagged similarly or handled separately
                # For now we use the same field or expect it to be handled in Cloud Run
                f.write(f"bot_rollback_revision={rollback_rev}\n") 
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
