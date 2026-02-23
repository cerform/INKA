#!/usr/bin/env python3
"""
Update the status of a release in the registry.
"""
import os
import sys
import argparse
import psycopg2

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--env", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--canary-percent", type=int, default=100)
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute(
            """
            UPDATE release_registry 
            SET status = %s, canary_percent = %s
            WHERE environment = %s AND version = %s
            """,
            (args.status, args.canary_percent, args.env, args.version)
        )
        
        if cur.rowcount == 0:
            print(f"⚠️ No record found to update: v{args.version} in {args.env}")
        else:
            print(f"✅ Status updated: v{args.version} ({args.env}) → {args.status}")
            
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
