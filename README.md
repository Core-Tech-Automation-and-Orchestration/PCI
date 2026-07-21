# PCI

CI/CD automation for the `cup-ecomm-greenzone` RPM package, migrated from Bamboo ([WMP-PCI](https://bamboo.int.cambridge.org/browse/WMP-PCI)) to GitHub Actions. This repo contains no application source — it holds the pipelines that build the RPM and deploy it to each environment via AWS Systems Manager (SSM) and CodeDeploy-style target group swaps.

## How it works

1. **Build** (`build-rpm.yaml`) — Runs on demand. Renders [task-template.json](task-template.json) into an ECS task definition, registers it, runs a one-off Fargate task that builds and publishes the `cup-ecomm-greenzone` RPM to the S3 repo (`S3_RPM_REPO`), then deregisters the task definition. On completion (success or failure), logs are pulled from CloudWatch and summarized with OpenAI (`gpt-5-mini`) into the job summary.
2. **Update versions** (`update-versions.yaml`) — Triggered automatically after `Build RPM Package` finishes (or manually). Lists all RPMs in `s3://pci-rpm-repo/`, regenerates [.github/versions.json](.github/versions.json) (newest first), and runs [update_dropdown.py](.github/scripts/update_dropdown.py) to rewrite the `deploy_version` choice list in every deployment workflow to the latest 10 versions. Changes are committed straight to `main`.
3. **Deploy** — One workflow per environment, each triggered manually via `workflow_dispatch` with a `deploy_version` selected from the dropdown:
   - [pci-eaq.yaml](.github/workflows/pci-eaq.yaml)
   - [pci-ejq.yaml](.github/workflows/pci-ejq.yaml)
   - [pci-erq.yaml](.github/workflows/pci-erq.yaml)
   - [pci-ert.yaml](.github/workflows/pci-ert.yaml)
   - [pci-staging.yaml](.github/workflows/pci-staging.yaml)
   - [pci-live.yaml](.github/workflows/pci-live.yaml)

   Each assumes an AWS IAM role via OIDC, then sends an SSM `AWS-RunShellScript` command to the target EC2 instance(s) that removes the current `cup-ecomm-greenzone` package and installs the selected version via `yum`. Command status is polled until success/failure, and stdout/stderr are written to the job summary.

   `pci-live.yaml` additionally performs a rolling deploy across two instances: each instance is deregistered from its ELBv2 target group before the RPM swap and re-registered (waiting for `target-in-service`) afterward, so the other instance keeps serving traffic during the update.

## Layout

```
.github/
  workflows/
    build-rpm.yaml       # builds & publishes the RPM via a one-off ECS Fargate task
    update-versions.yaml # regenerates versions.json and syncs dropdowns after a build
    pci-eaq.yaml          pci-ejq.yaml
    pci-erq.yaml          pci-ert.yaml
    pci-staging.yaml      pci-live.yaml
  scripts/
    update_dropdown.py   # rewrites deploy_version choices in each workflow from versions.json
    summarize_logs.py     # summarizes ECS build logs via OpenAI, appended to job summary
  versions.json           # cached, sorted list of RPM versions available in S3
task-template.json         # ECS Fargate task definition template (envsubst'd at build time)
```

## Required secrets & variables

| Name | Used by | Purpose |
|---|---|---|
| `IAM_ROLE` | all workflows | Role assumed via OIDC for AWS access |
| `AWS_REGION` | all workflows | Target AWS region |
| `ECS_EXEC_ROLE_ARN`, `ECS_TASK_ROLE_ARN`, `ECS_IMAGE` | build-rpm | ECS task definition fields |
| `OPENAI_API_KEY` | build-rpm | Log summarization |
| `ACTIONS_PAT` | update-versions | Push access to commit `versions.json`/workflow updates to `main` |
| `TASK_DEF_NAME`, `CONTAINER_NAME`, `CODECOMMIT_BRANCH`, `CODECOMMIT_REPO`, `S3_RPM_REPO` (vars) | build-rpm | ECS/task naming and source repo reference |
| `PCI_EAQ_INSTANCE_ID`, `STAGING_INSTANCE_ID`, `PCI_LIVE_INSTANCE_ID_1/2`, `PCI_LIVE_TARGET_GROUP_ARN` (vars) | respective deploy workflows | Target instance/ELB identifiers |

## Notes

- Deploy version dropdowns are auto-maintained — don't hand-edit the `options:` list in a `pci-*.yaml` workflow; it will be overwritten by the next `update-versions` run.
- `update-versions.yaml` pushes directly to `main` using a PAT, bypassing normal PR review — this is intentional for keeping the dropdowns in sync with S3.
