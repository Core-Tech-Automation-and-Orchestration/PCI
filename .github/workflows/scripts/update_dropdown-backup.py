import json
import re
from pathlib import Path

versions_file = Path(".github/versions.json")
workflow_file = Path(".github/workflows/learning-dev.yaml")

with open(versions_file) as f:
    versions = json.load(f)["versions"]

versions = versions[:10]

choice_block = "\n".join([f"          - {v}" for v in versions])

content = workflow_file.read_text()

# Replace the deploy_version options block dynamically
new_content = re.sub(
    r"(deploy_version:[\s\S]*?options:\n)(?:[ \t]*- .*\n)*",
    rf"\1{choice_block}\n",
    content,
)

if content.strip() == new_content.strip():
    print("ℹ️ No changes detected in version list — skipping update.")
else:
    workflow_file.write_text(new_content)
    print(f"✅ Updated {workflow_file} with {len(versions)} version(s):")
    for v in versions:
        print(f"  - {v}")
