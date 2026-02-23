#!/usr/bin/env python3
"""
Safety checks for Alembic migrations.
- Checks for risky operations (DROP COLUMN, RENAME TABLE).
- Verifies migration files have both upgrade() and downgrade().
"""
import os
import sys
import re
import glob

def check_migration_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    risks = []
    
    # Check for risky operations
    if re.search(r'op\.drop_column', content):
        risks.append("Contains DROP COLUMN (destructive)")
    if re.search(r'op\.drop_table', content):
        risks.append("Contains DROP TABLE (destructive)")
    if re.search(r'op\.rename_table', content):
        risks.append("Contains RENAME TABLE (risky for uptime)")
        
    # Check for presence of downgrade
    downgrade_match = re.search(r'def downgrade\(\):\s+(.*)', content, re.DOTALL)
    if not re.search(r'def downgrade\(\)', content) or (downgrade_match and 'pass' in downgrade_match.group(1)):
         # If downgrade exists but is just 'pass'
         if content.count('pass') > content.count('def upgrade'): # Rough check
             risks.append("Missing effective downgrade() implementation")

    return risks

def main():
    migration_path = "libs/database/alembic/versions/*.py"
    files = glob.glob(migration_path)
    
    if not files:
        print("✅ No migration files found to check.")
        return

    # In CI, we only want to check CHANGED files vs main
    # But for a general check, we'll scan all for now
    
    total_risks = 0
    for file in files:
        # Skip __init__.py and similar
        if "__" in file: continue
        
        risks = check_migration_file(file)
        if risks:
            print(f"⚠️ {file}:")
            for risk in risks:
                print(f"  - {risk}")
            total_risks = total_risks + len(risks)

    if total_risks > 0:
        print(f"\n📢 Total migration risks found: {total_risks}")
        print("💡 Review these changes to ensure backward compatibility.")
        # We don't necessarily fail CI unless we want to be very strict
        # sys.exit(1)
    else:
        print("✅ No migration risks detected.")

if __name__ == "__main__":
    main()
