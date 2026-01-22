import json
import re
from pathlib import Path

versions_file = Path(".github/versions.json")
workflow_dir = Path(".github/workflows")

workflow_files = [
    "pci-eaq.yaml",
    "pci-ejq.yaml",
    "pci-erq.yaml",
    "pci-ert.yaml",
    "pci-live.yaml",
    "pci-staging.yaml"
]

with open(versions_file) as f:
    versions = json.load(f)["versions"]

versions = versions[:10]
choice_block = "\n".join([f"          - {v}" for v in versions])
pattern = re.compile(r"(deploy_version:[\s\S]*?options:\n)(?:[ \t]*- .*\n)*")
changed_files = 0

print("Checking workflows for version updates...\n")
for wf_name in workflow_files:
    wf_path = workflow_dir / wf_name

    if not wf_path.exists():
        print(f"{wf_name} not found — skipping.")
        continue

    content = wf_path.read_text()
    new_content = re.sub(pattern, rf"\1{choice_block}\n", content)

    if content.strip() == new_content.strip():
        print(f"No changes detected in {wf_name} — skipping update.")
    else:
        wf_path.write_text(new_content)
        changed_files += 1
        print(f"Updated {wf_name} with {len(versions)} version(s):")
        for v in versions:
            print(f"  - {v}")
        print()
if changed_files == 0:
    print("All workflow files already up to date.")
else:
    print(f"{changed_files} workflow file(s) updated successfully.")