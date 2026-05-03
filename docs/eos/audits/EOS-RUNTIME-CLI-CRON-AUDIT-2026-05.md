# EOS Runtime CLI/Cron Audit 2026-05

## Scope

Audit für EOS Runtime, CLI, Cron/Systemd-Smoke, lokale Tooling-Abhängigkeiten und den gemeldeten Telekom-Paket-Hinweis. Diese Prüfung interpretiert "EOSD Crunch" als EOS Cron/CLI Runtime. Falls damit ein anderes System gemeint war, muss dieser Audit ergänzt werden.

## Ausgeführte Befehle

```bash
python scripts/eos_runtime_doctor.py
python3 scripts/eos_runtime_doctor.py
bash scripts/run_eos_cli_smoke.sh
bash scripts/run_eos_cron_smoke.sh
python -m pytest tests/verify_runtime_doctor.py -q
python3 -m pytest tests/verify_runtime_doctor.py -q
python -m pytest -q
python3 -m pytest -q
python3 -m pytest --collect-only -q
git diff --check
python -m pip list | grep -i telekom || true
python -m pip freeze | grep -i telekom || true
python3 -m pip list | grep -i telekom || true
python3 -m pip freeze | grep -i telekom || true
python3 - <<'PY'
import pkgutil
mods = sorted(m.name for m in pkgutil.iter_modules() if "telekom" in m.name.lower())
print(mods)
PY
```

## Ergebnisse

- `python scripts/eos_runtime_doctor.py`: failed, `python` alias is missing.
- `python3 scripts/eos_runtime_doctor.py`: success, doctor returned `status=warning`.
- Doctor import checks: `src.eos_cli=success`, `src.runtime=success`.
- Doctor tool checks: `pytest=success`, `gh=success`, `systemctl=success`, `gog=missing`.
- Doctor Python checks: `python3=success`, `python=missing`, `pip=missing` for `/usr/bin/python3`.
- `bash scripts/run_eos_cli_smoke.sh`: success exit. CLI help works; health returns `warning`; `cron-audit` and `model-audit` return `success`; daily-plan dry-run returns `yellow`; weekly-plan dry-run returns `success`.
- `bash scripts/run_eos_cron_smoke.sh`: success exit. Systemd timer listing returned EOS timers.
- `python3 -m pytest tests/verify_runtime_doctor.py -q`: success, 5 passed.
- `python3 -m pytest -q`: failed with no tests collected. This is a pytest discovery gap on `origin/main`, where existing smoke tests are named `verify_*.py`.
- `git diff --check`: success.

## Fehlerklassen

- Code-Regressionsfehler: EOS-Import oder CLI-Smoke bricht reproduzierbar durch Codefehler.
- Fehlende Secrets: Health oder Gateway-Checks liefern Warnungen wegen nicht konfigurierter externer Dienste.
- Fehlende lokale Tools: `python`, `pip`, `gog`, `gh` oder `systemctl` fehlen.
- Telekom-/Dependency-Konflikt: Paket, Modul oder lokale Datei mit `telekom` im Namen beeinflusst Import oder Runtime.
- Systemd nicht verfügbar: `systemctl` fehlt oder Systemd läuft im lokalen Container nicht.
- Unbekannt: Fehler muss mit vollständigem Command-Output erneut klassifiziert werden.

## Telekom-Paket

Kein Telekom-Paket oder Telekom-Modul wurde gefunden.

- `python -m pip list | grep -i telekom || true`: `python` alias missing.
- `python -m pip freeze | grep -i telekom || true`: `python` alias missing.
- `python3 -m pip list | grep -i telekom || true`: `pip` missing for `/usr/bin/python3`.
- `python3 -m pip freeze | grep -i telekom || true`: `pip` missing for `/usr/bin/python3`.
- `pkgutil.iter_modules()`: `[]`.
- Runtime Doctor: `telekom_related_packages=[]`, `telekom_related_modules=[]`, `local_telekom_conflicts=[]`.

## CLI-Status

- CLI entry point: `python3 -m src.eos_cli --help` succeeds.
- `health`: warning because the repo vault folders are partially missing in this checkout; Google Tasks, calendar, cron, model, and habit checks succeeded locally.
- `cron-audit`: success, 9 jobs found, 5 enabled, no issues.
- `model-audit`: success, no issues.
- `daily-plan --dry-run`: yellow, triage/review required from live task state.
- `weekly-plan --dry-run`: success.

The smoke scripts mask Telegram delivery targets and obvious token/secret fields. Full dry-run output can contain live calendar/task data and should not be pasted into public reports.

## Cron-Status

- `ops/systemd` contains EOS timer/service files.
- `cron-audit`: success.
- `systemctl list-timers --all | grep -i eos`: success in this environment and returned EOS timers.

## Offene Risiken

- `python` is not available in this environment; Runtime scripts default to `python3`.
- `pip` is not available through `/usr/bin/python3`; the Doctor uses `importlib.metadata` and `pkgutil` as fallback diagnostics.
- `gog` is not available on `PATH` according to `shutil.which`, although the existing CLI can still read live `gog`-backed calendar/task data through its configured gateway.
- Global `python3 -m pytest -q` does not collect existing `verify_*.py` smoke tests without explicit file paths or pytest configuration.
- Full CLI dry-run output can include live personal calendar/task data. Reports should summarize status and error classes only.

## Konkrete nächste Schritte

1. Decide whether to add a repo-level pytest discovery config for `verify_*.py` in a separate owner-approved change.
2. Decide whether CLI health/dry-run commands need a public-safe summary mode before sharing smoke output outside the local machine.
3. Keep diagnosing Telekom only if the user can provide the exact failing package/module name from their environment.
