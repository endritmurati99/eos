# EOS Local Development Environment Audit - 2026-05

## Summary

The local Codex/GitHub problem is a workspace and Git setup issue, not evidence that Codex itself is broken.

Codex was initially running from:

```text
/docker/openclaw-qt6t
```

That directory is an OpenClaw/Solara wrapper with no Git remote. The real EOS repo is:

```text
/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
```

## Current Start Folder

```text
current_directory=/docker/openclaw-qt6t
git_toplevel=/docker/openclaw-qt6t
branch=agent3/security-retention-google-live-gates
origin_present=yes
origin_url=https://github.com/endritmurati99/eos.git
latest_commit=44dbe0f chore: initial Solara project import
repo_kind=openclaw_wrapper
```

This folder should not be used for EOS branch, push, or PR work. Its Git history is Solara/OpenClaw-wrapper context even though its current `origin` points to EOS, which is a dangerous workspace mismatch.

## Real EOS Folder

```text
eos_workspace=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
git_toplevel=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
branch_at_audit_start=main
repo_kind=eos
```

EOS identity checks found:

```text
src/eos_cli.py
src/database/models.py
src/jobs
AGENTS.md
origin=https://github.com/endritmurati99/eos.git
```

Existing local dirty files observed and intentionally left untouched:

```text
.learnings/ERRORS.md
data/eos_v2.db
.openclaw.code-workspace
memory/2026-05-02.md
memory/2026-05-03.md
```

## Git Remote Status

EOS remote:

```text
origin=https://github.com/endritmurati99/eos.git
```

Fetch status:

```text
git_fetch_origin_status=ok
```

Branch list includes `origin/main` and multiple agent branches.

## GitHub CLI Status

```text
gh_available=yes
gh_version=2.45.0
gh_auth_status=authenticated_as_endritmurati99
gh_git_protocol=https
gh_repo_view_status=ok
gh_pr_list_status=ok
```

No token values were recorded in this audit.

## SSH Status

```text
ssh_github_status=failed_host_key_verification
ssh_private_key_observed=no
```

Observed command result:

```text
ssh -T git@github.com -> Host key verification failed.
```

`~/.ssh` contained `authorized_keys` but no private SSH key files. Use HTTPS remote and `gh auth` until SSH is configured.

## Codex Status

```text
codex_available=yes
codex_path=/usr/local/bin/codex
codex_version=codex-cli 0.128.0
bwrap_available=yes
bwrap_version=0.9.0
```

Codex CWD risk:

```text
If Codex starts in /docker/openclaw-qt6t, it sees the wrapper repo with no origin.
If Codex starts in /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant, it sees EOS with the correct origin.
```

## Concrete Next Commands

Use this for EOS work:

```bash
cd /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
git status --short --branch
git remote -v
git fetch origin
gh pr list --repo endritmurati99/eos --state open
codex
```

Use this for forced Codex CWD:

```bash
codex -C /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
```

Use this for diagnostics:

```bash
bash scripts/eos_repo_locator.sh
bash scripts/eos_git_gh_doctor.sh
python3 scripts/eos_env_doctor.py
```

## AGENT_4_STATUS

```text
current_directory=/docker/openclaw-qt6t
git_toplevel=/docker/openclaw-qt6t
repo_kind=openclaw_wrapper
eos_workspace_found=yes
eos_workspace_path=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
origin_present=yes
origin_url=https://github.com/endritmurati99/eos.git
origin_added=no
git_fetch_origin_status=ok
gh_available=yes
gh_auth_status=authenticated
gh_repo_view_status=ok
ssh_github_status=failed_host_key_verification
codex_available=yes
codex_version=codex-cli 0.128.0
likely_root_cause=codex_or_extension_started_in_wrapper_repo_instead_of_eos_workspace
wrapper_remote_risk=wrapper_has_eos_origin_but_not_eos_history
recommended_cd=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
scripts_created=yes
docs_created=yes
pushed=yes
pr_created=yes
pr_url=https://github.com/endritmurati99/eos/pull/15
secrets_printed=no
blocking_risks=ssh_not_configured_for_github_but_https_gh_path_works
next_recommended_step=start_codex_from_recommended_cd
```
