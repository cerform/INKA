#!/usr/bin/env python3
"""
Log a rollback incident in the release registry.
"""
import os
import sys
import uuid
from datetime import datetime, timezone
import psycopg2

def main():
    db_url = os.environ.get("DATABASE_URL")
    environment = os.environ.get("ENVIRONMENT")
    reason = os.environ.get("REASON", "Manual rollback")
    actor = os.environ.get("ROLLED_BACK_BY", "system")

    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. Mark current (failed) release as ROLLED_BACK
        cur.execute(
            """
            UPDATE release_registry 
            SET status = 'ROLLED_BACK' 
            WHERE environment = %s AND status = 'DEPLOYED'
            """,
            (environment,)
        )
        
        # 2. Add an audit entry for the rollback itself (optional, but good practice)
        # We can reuse the release_registry with a 'ROLLBACK' status or similar
        cur.execute(
            """
            INSERT INTO release_registry (
                id, version, environment, git_sha, deployed_by, 
                deployed_at, status, rollback_revision
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(uuid.uuid4()),
                "ROLLBACK",
                environment,
                "N/A",
                actor,
                datetime.now(timezone.utc),
                "ROLLBACK_EXECUTED",
                reason
            )
        )
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Rollback incident logged for {environment}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
