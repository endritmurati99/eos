from __future__ import annotations

import importlib
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))


def test_runtime_import_does_not_crash() -> None:
    runtime = importlib.import_module("src.runtime")

    assert runtime.WORKSPACE_ROOT == WORKSPACE_ROOT
    assert isinstance(runtime.CRON_JOBS_PATH, Path)
    assert isinstance(runtime.CRON_RUNS_DIR, Path)
    assert isinstance(runtime.AGENT_MODELS_PATH, Path)


def test_discover_openclaw_root_with_root_checkout(monkeypatch, tmp_path: Path) -> None:
    runtime = importlib.import_module("src.runtime")
    checkout = tmp_path / "checkout"
    (checkout / "data" / ".openclaw").mkdir(parents=True)
    monkeypatch.delenv("EOS_OPENCLAW_ROOT", raising=False)

    assert runtime.discover_openclaw_root(checkout) == checkout.resolve()


def test_discover_openclaw_root_with_nested_workspace(monkeypatch, tmp_path: Path) -> None:
    runtime = importlib.import_module("src.runtime")
    host_data = tmp_path / "host" / "data"
    workspace = host_data / ".openclaw" / "workspaces" / "personal-assistant"
    workspace.mkdir(parents=True)
    monkeypatch.delenv("EOS_OPENCLAW_ROOT", raising=False)

    assert runtime.discover_openclaw_root(workspace) == host_data.resolve()


def test_eos_openclaw_root_overrides_discovery(monkeypatch, tmp_path: Path) -> None:
    runtime = importlib.import_module("src.runtime")
    override = tmp_path / "explicit-openclaw-root"
    nested = tmp_path / "elsewhere" / "data" / ".openclaw" / "workspaces" / "personal-assistant"
    nested.mkdir(parents=True)
    monkeypatch.setenv("EOS_OPENCLAW_ROOT", str(override))

    assert runtime.discover_openclaw_root(nested) == override.resolve()


def test_missing_openclaw_structure_falls_back_without_crashing(monkeypatch, tmp_path: Path) -> None:
    runtime = importlib.import_module("src.runtime")
    plain_checkout = tmp_path / "plain"
    plain_checkout.mkdir()
    monkeypatch.delenv("EOS_OPENCLAW_ROOT", raising=False)

    assert runtime.discover_openclaw_root(plain_checkout) == runtime.WORKSPACE_ROOT
