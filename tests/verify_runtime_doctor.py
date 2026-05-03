#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts import eos_runtime_doctor


def test_runtime_doctor_returns_json_serializable_dict(tmp_path: Path) -> None:
    payload = eos_runtime_doctor.run_doctor(workspace_root=tmp_path)

    assert isinstance(payload, dict)
    assert payload["status"] in {"success", "warning", "error"}
    assert payload["python"]["version"]
    assert "src.eos_cli" in payload["imports"]
    assert "src.runtime" in payload["imports"]
    json.dumps(payload)


def test_environment_values_are_masked(monkeypatch) -> None:
    secret = "raw-secret-value-that-must-not-print"
    monkeypatch.setenv("EOS_DB_PATH", secret)

    environment = eos_runtime_doctor.collect_environment(("EOS_DB_PATH",))
    serialized = json.dumps(environment)

    assert environment["EOS_DB_PATH"]["set"] is True
    assert environment["EOS_DB_PATH"]["value"] == f"<masked:{len(secret)}>"
    assert secret not in serialized


def test_telekom_scan_does_not_crash(tmp_path: Path) -> None:
    result = eos_runtime_doctor.scan_telekom_dependencies(tmp_path)

    assert sorted(result) == [
        "local_telekom_conflicts",
        "telekom_related_modules",
        "telekom_related_packages",
    ]
    assert isinstance(result["telekom_related_packages"], list)
    assert isinstance(result["telekom_related_modules"], list)
    assert result["local_telekom_conflicts"] == []


def test_missing_gog_is_warning_not_crash(monkeypatch, tmp_path: Path) -> None:
    original_which = eos_runtime_doctor.shutil.which

    def fake_which(name: str) -> str | None:
        if name == "gog":
            return None
        return original_which(name)

    monkeypatch.setattr(eos_runtime_doctor.shutil, "which", fake_which)

    payload = eos_runtime_doctor.run_doctor(workspace_root=tmp_path)

    assert payload["tools"]["gog"]["status"] == "missing"
    assert payload["status"] in {"warning", "error"}
    assert any(issue["code"] == "tool_missing" and issue["name"] == "gog" for issue in payload["issues"])


def test_import_checks_run() -> None:
    imports = {
        "src.eos_cli": eos_runtime_doctor.check_import("src.eos_cli"),
        "src.runtime": eos_runtime_doctor.check_import("src.runtime"),
    }

    assert imports["src.eos_cli"]["status"] == "success"
    assert imports["src.runtime"]["status"] == "success"


if __name__ == "__main__":
    os.environ.setdefault("EOS_DB_PATH", str(WORKSPACE_ROOT / ".runtime-doctor-test.db"))
    raise SystemExit(0)
