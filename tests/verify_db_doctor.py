from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts import eos_db_doctor  # noqa: E402


def test_db_doctor_default_uses_untracked_runtime_db(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EOS_DB_PATH", raising=False)

    payload = eos_db_doctor.run_doctor(workspace_root=tmp_path)

    assert payload["status"] == "success"
    assert payload["db_path"] == str((tmp_path / "var" / "eos_v2.db").resolve())
    assert payload["db_path_source"] == "default_runtime"
    assert payload["legacy_repo_db_used"] is False


def test_db_doctor_success_with_temp_sqlite_path(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "state" / "eos.db"
    db_path.parent.mkdir()
    monkeypatch.setenv("EOS_DB_PATH", str(db_path))

    payload = eos_db_doctor.run_doctor()

    assert payload["status"] == "success"
    assert payload["exists"] is True
    assert payload["parent_writable"] is True
    assert payload["db_writable"] is True
    assert payload["sqlite_write_probe"] == "success"
    json.dumps(payload)


def test_db_doctor_uses_eos_db_path_override(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "override.db"
    monkeypatch.setenv("EOS_DB_PATH", str(db_path))

    payload = eos_db_doctor.run_doctor(sqlite_probe=False)

    assert payload["db_path"] == str(db_path.resolve())
    assert payload["db_path_source"] == "EOS_DB_PATH"


def test_readonly_db_file_is_reported_even_when_effective_user_is_root(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "readonly.db"
    db_path.touch()
    db_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    monkeypatch.setenv("EOS_DB_PATH", str(db_path))

    try:
        payload = eos_db_doctor.run_doctor(sqlite_probe=False)
    finally:
        db_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    assert payload["status"] == "failed"
    assert payload["db_writable"] is False
    assert any(issue["code"] == "db_not_writable" for issue in payload["issues"])


def test_parent_not_writable_is_reported_even_when_effective_user_is_root(monkeypatch, tmp_path: Path) -> None:
    parent = tmp_path / "readonly-parent"
    parent.mkdir()
    parent.chmod(stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
    db_path = parent / "eos.db"
    monkeypatch.setenv("EOS_DB_PATH", str(db_path))

    try:
        payload = eos_db_doctor.run_doctor(sqlite_probe=False)
    finally:
        parent.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    assert payload["status"] == "failed"
    assert payload["parent_writable"] is False
    assert any(issue["code"] == "parent_not_writable" for issue in payload["issues"])


def test_secret_like_environment_values_are_not_serialized(monkeypatch, tmp_path: Path) -> None:
    secret = "raw secret sentinel phrase that must not appear"
    db_path = tmp_path / "safe.db"
    monkeypatch.setenv("EOS_DB_PATH", str(db_path))
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", secret)

    payload = eos_db_doctor.run_doctor(sqlite_probe=False)
    serialized = json.dumps(payload)

    assert secret not in serialized


def test_target_owner_writeability_can_detect_service_user_mismatch(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "root_owned_mode_0644.db"
    db_path.touch()
    db_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    monkeypatch.setenv("EOS_DB_PATH", str(db_path))
    monkeypatch.setenv("EOS_DB_OWNER_USER", "definitely_missing_eos_user")
    monkeypatch.setenv("EOS_DB_OWNER_GROUP", "definitely_missing_eos_group")

    payload = eos_db_doctor.run_doctor(sqlite_probe=False)

    assert payload["target_identity"]["configured"] is True
    assert payload["target_identity"]["resolved"] is False
    assert payload["status"] == "warning"
    assert any(issue["code"] == "target_identity_unresolved" for issue in payload["issues"])
