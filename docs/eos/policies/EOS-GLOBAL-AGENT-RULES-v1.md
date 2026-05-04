# EOS Global Agent Rules v1

Status: required for all implementation agents

## Purpose

These rules apply to every EOS implementation task. They protect `main`, prevent accidental secret exposure, and keep every change verifiable and reportable.

## Branching

Never push directly to `main`.

For a clean worktree, start from updated `main`:

```bash
git fetch origin
git checkout main
git pull origin main
git checkout -b <branch-name>
```

If the worktree already contains uncommitted task work on `main`, create the feature branch before pulling or committing:

```bash
git checkout -b <branch-name>
git fetch origin
```

Then inspect whether rebasing or merging from `origin/main` is safe before doing it. Do not risk losing local work.

Push work to the feature branch, not `main`:

```bash
git add .
git commit -m "<clear message>"
git push -u origin <branch-name>
```

If the branch already exists upstream:

```bash
git push
```

## GitHub CLI

Use GitHub CLI when available:

```bash
gh repo view
gh pr create --fill
```

If GitHub CLI is unavailable or unauthenticated, use normal git commands and report that PR creation was not completed.

## Safety

Do not touch secrets.

Do not:

- print tokens
- modify `.env` with real credentials
- add Gmail write scopes unless explicitly requested
- send real Gmail messages
- delete real Gmail messages
- archive real Gmail messages
- unsubscribe from real Gmail messages
- label real Gmail messages

Do not inspect token or credential file contents unless the user explicitly asks for that exact security task. Even then, avoid printing secret values.

## Verification

Every implementation task must run the project test command.

Default command:

```bash
python -m pytest
```

If `python` is unavailable on the host, use:

```bash
python3 -m pytest
```

If the repo has a different test command, detect and run the repo-specific command as well.

For this repository, `pytest` may collect no tests because the current smoke checks are script-style `tests/verify_*.py` files. Run them explicitly:

```bash
for f in tests/verify_*.py; do
  python3 "$f"
done
```

Also run lightweight CLI smoke checks when available:

```bash
python3 -m src.eos_cli --help
```

For documentation or policy changes, also run:

```bash
git diff --check
```

## Reporting

Every implementation response must end with:

```text
BRANCH:
COMMITS:
FILES_CHANGED:
TESTS_RUN:
TEST_RESULT:
OPEN_RISKS:
NEXT_RECOMMENDED_STEP:
```

Use exact branch and commit IDs where available. If a test command fails because the host lacks a binary or because pytest collects no tests, report the exact result and the fallback command that was run.

## Round 1 Merge Order

For the current EOS Phase 0 round, merge in this order:

```text
1. Agent 1 first
2. Agent 2 after rebasing on Agent 1
3. Agent 3 last, after rebasing on the merged result
```

Reason:

- Agent 1 establishes policies and structure.
- Agent 2 and Agent 3 should build on that shared baseline.

## Hard Stops

Stop and ask before proceeding if:

- the task requires pushing to `main`
- a command would reveal secrets
- Gmail write scopes are requested implicitly rather than explicitly
- a real external write would happen without approval
- the branch has diverged and automatic rebase would risk overwriting user work
