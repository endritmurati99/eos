# EOS Local Development Environment Runbook

## 1. Goal

This runbook keeps Codex, Claude Code, SSH terminals, Git, and GitHub CLI pointed at the real EOS repository:

```bash
/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
```

The expected GitHub repository is:

```text
endritmurati99/eos
```

## 2. Why Codex or GitHub Access Can Fail

The most common failure is workspace mismatch, not a broken Codex installation.

Known local pattern:

```text
/docker/openclaw-qt6t
```

is an OpenClaw/Solara wrapper repo. It may have no `origin` remote and should not be used for EOS feature, branch, or PR work.

Codex works in the current working directory where it was started. If it starts in the wrapper, it sees the wrapper Git repository, not EOS.

If the wrapper has an `origin` that points to `endritmurati99/eos`, that is still not enough to make it the EOS repo. Check the EOS markers before doing branch, push, or PR work.

## 3. OpenClaw Wrapper vs Real EOS Workspace

Do not treat the wrapper as EOS. The real EOS workspace must satisfy at least two of these checks:

```text
- contains src/eos_cli.py
- contains docs/eos/**
- contains src/database/models.py
- contains src/jobs/**
- contains AGENTS.md or EOS-MASTER-CONTEXT.md
- git remote points to endritmurati99/eos
```

The current real EOS workspace satisfies multiple checks:

```text
src/eos_cli.py
src/database/models.py
src/jobs
AGENTS.md
origin=https://github.com/endritmurati99/eos.git
```

## 4. Find the Right Workspace

Run:

```bash
cd /docker/openclaw-qt6t
bash data/.openclaw/workspaces/personal-assistant/scripts/eos_repo_locator.sh
```

Or from inside EOS:

```bash
cd /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
bash scripts/eos_repo_locator.sh
```

Use the candidate that reports EOS markers and the `endritmurati99/eos` remote.

## 5. Set or Check origin Remote

First inspect:

```bash
cd /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
git remote -v
```

Expected working local state:

```text
origin  https://github.com/endritmurati99/eos.git (fetch)
origin  https://github.com/endritmurati99/eos.git (push)
```

Only add `origin` when the directory is clearly EOS:

```bash
git remote add origin git@github.com:endritmurati99/eos.git
git fetch origin
```

If SSH is not configured, use HTTPS:

```bash
git remote set-url origin https://github.com/endritmurati99/eos.git
git fetch origin
```

Do not set an EOS remote in the OpenClaw wrapper or in Solara. If such a remote is already present there, treat it as `wrong_workspace` until the Git history and EOS markers prove the directory is the real EOS repo.

## 6. Check GitHub CLI Auth

Run:

```bash
which gh
gh --version
gh auth status
gh repo view endritmurati99/eos
gh pr list --repo endritmurati99/eos --state open
```

If `gh auth status` fails, authenticate interactively:

```bash
gh auth login
```

Do not print tokens. Do not save tokens in repo files. Do not paste token screenshots into issues or PRs.

## 7. Check SSH

Run:

```bash
ssh -T git@github.com || true
ls -la ~/.ssh || true
```

Local status observed on 2026-05-04:

```text
ssh -T git@github.com -> Host key verification failed.
~/.ssh contains no private key files.
```

This means HTTPS Git operations through `gh` are the reliable path on this host until SSH host keys and private keys are configured.

## 8. Start Codex in the Right CWD

Codex is available locally:

```bash
which codex
codex --version
```

Start Codex from EOS:

```bash
cd /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
codex
```

Or force the working root:

```bash
codex -C /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
```

If Codex starts in `/docker/openclaw-qt6t`, it will inspect the wrapper repository and may report no `origin` remote.

## 9. VS Code Extension vs SSH Terminal

The difference is real.

VS Code extension sessions can:

```text
- start in a different workspace or CWD
- see a repo without an origin remote
- use a different PATH
- use different GitHub or SSH auth context
- start Codex or Claude in the wrapper directory
```

SSH terminal sessions show the actual server context:

```text
- Git, gh, SSH, and Codex depend on the current directory
- gh auth and SSH keys are user and host specific
- SSH terminal is better for first diagnosis and repo setup
```

## 10. Standard Flow for New Agents

Every EOS agent should start with:

```bash
cd /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
git status --short --branch
git remote -v
git fetch origin
gh pr list --repo endritmurati99/eos --state open
```

Then create a task branch:

```bash
git checkout main
git pull origin main
git checkout -b agent-name/task-name || git checkout agent-name/task-name
```

## 11. Error Classes

Use these labels in audits and handoffs:

```text
wrong_workspace: Codex or shell is in wrapper/Solara, not EOS.
missing_origin: EOS repo has no origin remote.
wrong_remote: origin does not point to endritmurati99/eos, or points to EOS from a non-EOS repo.
ssh_key_missing: SSH key files are absent.
ssh_host_key_failed: GitHub SSH host key is not trusted or known_hosts is missing.
gh_not_authenticated: gh auth status fails.
repo_access_missing: gh is logged in but cannot view endritmurati99/eos.
network_issue: DNS, TLS, or network connection fails.
codex_missing: codex binary is not on PATH.
codex_wrong_cwd: codex starts outside the EOS workspace.
```

## 12. What Not To Do

Do not:

```text
- add EOS origin to the OpenClaw wrapper
- add EOS origin to Solara
- print tokens or secrets
- write tokens into files
- inspect .env, credentials, tokens, or data files unless explicitly needed for a separate task
- push while repo identity is unclear
- do EOS feature work from /docker/openclaw-qt6t
```

## Quick Doctor Commands

From the EOS workspace:

```bash
cd /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant
bash scripts/eos_repo_locator.sh
bash scripts/eos_git_gh_doctor.sh
python3 scripts/eos_env_doctor.py
```
