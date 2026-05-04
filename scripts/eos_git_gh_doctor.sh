#!/usr/bin/env bash
set -euo pipefail

echo "== EOS Git/GH Doctor =="
echo "pwd=$(pwd)"

echo ""
echo "== git =="
git --version || true
git rev-parse --show-toplevel || true
git status --short --branch || true
git remote -v || true

echo ""
echo "== gh =="
which gh || true
gh --version || true
gh auth status || true
gh repo view endritmurati99/eos || true
gh pr list --repo endritmurati99/eos --state open || true

echo ""
echo "== ssh =="
ssh -T git@github.com || true

echo ""
echo "== codex =="
which codex || true
codex --version || true
