# EOS Runtime CLI/Cron Testing Runbook

## Ziel

Dieses Runbook beschreibt, wie EOS Runtime, CLI, Cron/Systemd-Konzept, lokale Tooling-Abhängigkeiten und der gemeldete Telekom-Paket-Hinweis reproduzierbar geprüft werden. Die Prüfungen führen keine Gmail-, OAuth-, Label-, Archiv-, Delete- oder Send-Aktionen aus und drucken keine Secrets.

## CLI testen

Standardprüfung:

```bash
python3 scripts/eos_runtime_doctor.py
bash scripts/run_eos_cli_smoke.sh
```

`scripts/run_eos_cli_smoke.sh` nutzt `${PYTHON_BIN:-python3}` und führt aus:

- `python3 -m src.eos_cli --help`
- `python3 -m src.eos_cli --json-only health`
- `python3 -m src.eos_cli --json-only cron-audit`
- `python3 -m src.eos_cli --json-only model-audit`
- `python3 -m src.eos_cli --json-only daily-plan --date "$(date +%F)" --dry-run`
- `python3 -m src.eos_cli --json-only weekly-plan --week-start "$(date +%F)" --dry-run`

Die Smoke-Kommandos werden intern mit separatem stdout/stderr Capture ausgeführt und anschließend über `scripts/eos_safe_smoke_summary.py` zusammengefasst. Die Skripte drucken keine Raw-Ausgabe aus CLI, Kalender, Tasks, Gmail, Telegram oder Environment.

Erlaubt sind nur Command-Name, Status, Exit-Code, Fehlerklasse und Output-Zeilenanzahlen. Wenn die Runtime mit `attempt to write a readonly database` fehlschlägt, muss die Fehlerklasse `readonly_database` erscheinen. Das ist ein P0-Runtime-Blocker, wird aber nicht durch dieses Smoke-Hardening repariert.

Wenn `EOS_DB_PATH` nicht gesetzt ist, verwenden die Smoke-Skripte eine temporäre DB. Dadurch wird `data/eos_v2.db` nicht durch Smoke verändert. Um den bekannten DB-Blocker gezielt zu reproduzieren, kann ein Operator `EOS_DB_PATH` explizit auf den betroffenen Runtime-Pfad setzen; die Ausgabe bleibt trotzdem redigiert.

Beispiel:

```text
EOS_SAFE_SMOKE
- cli_help: pass exit_code=0 stdout_lines=20 stderr_lines=0 sensitive_output_detected=no raw_output_printed=no
- health: warning exit_code=1 error_class=readonly_database stdout_lines=0 stderr_lines=12 sensitive_output_detected=no raw_output_printed=no
- sensitive_output_printed: no
```

## Cron/Systemd testen

Standardprüfung:

```bash
bash scripts/run_eos_cron_smoke.sh
```

Das Skript prüft `ops/` Systemd-Dateien, führt `cron-audit` aus und fragt Systemd-Timer ab, falls `systemctl` verfügbar ist. Die Ergebnisse werden nur als sichere Summary ausgegeben. In Container- oder CI-Umgebungen kann `systemctl` installiert sein, aber ohne laufenden Systemd-Daemon fehlschlagen. Das ist ein Environment-Problem, kein direkter EOS-Codefehler.

Auch dieses Skript druckt keine Timer-Rohdaten, Telegram-Ziele oder Secret-Felder.

## Safe Smoke Summary

`scripts/eos_safe_smoke_summary.py` klassifiziert bekannte Runtime-/Environment-Fehler:

- `readonly_database`
- `missing_gog`
- `missing_systemctl`
- `missing_python_alias`
- `missing_secrets`
- `provider_auth_required`
- `environment_issue`
- `real_code_failure`
- `unknown`

Bekannte Runtime-/Environment-Fehler führen im Smoke zu `warning`, damit CI nicht wegen eines bereits klassifizierten Infrastrukturzustands hart fehlschlägt. `real_code_failure` und unbekannte Non-Zero-Fehler bleiben `failed`.

Selbsttest:

```bash
python3 scripts/eos_safe_smoke_summary.py --self-test
```

## Dependency-Konflikte prüfen

Der Runtime Doctor prüft:

- Python-Version und ausführbares Python
- `python` und `python3` Aliase
- `pip` über `sys.executable -m pip --version`
- Importfähigkeit von `src.eos_cli` und `src.runtime`
- Verfügbarkeit von `pytest`, `gog`, `gh` und `systemctl`
- gekürzten `sys.path`
- relevante Environment-Variablennamen mit maskierten Werten

Kritisch sind Importfehler für EOS-Module oder reproduzierbare CLI-Abbrüche in Kommandos, die ohne externe Secrets laufen sollten.

## Telekom-Paket-Diagnose

Manuelle Zusatzprüfung:

```bash
python -m pip list | grep -i telekom || true
python -m pip freeze | grep -i telekom || true
python3 - <<'PY'
import pkgutil
mods = sorted(m.name for m in pkgutil.iter_modules() if "telekom" in m.name.lower())
print(mods)
PY
```

Wenn ein Telekom-Paket gefunden wird:

- Paketname, Version und Importpfad dokumentieren.
- Prüfen, ob es `src.eos_cli` oder `src.runtime` beeinflusst.
- Nicht blind deinstallieren.

Wenn nur `pip` fehlt, aber `pkgutil` keinen Telekom-Fund liefert, ist das ein lokales Tooling-Problem und kein belegter Telekom-Konflikt.

## Kritische Fehler

- `src.eos_cli` oder `src.runtime` nicht importierbar.
- `python3 -m src.eos_cli --help` schlägt fehl.
- `cron-audit` oder `model-audit` crashen statt JSON auszugeben.
- Secrets erscheinen unmaskiert im Doctor-Output.
- Ein lokaler `telekom`-Namenskonflikt überschattet EOS-Module.

## Environment-Probleme

- `python` fehlt, wenn `python3` verfügbar ist.
- `pip` fehlt lokal.
- `gog` fehlt lokal.
- `systemctl` ist installiert, aber Systemd läuft nicht.
- Google/Telegram Secrets fehlen und Health-Checks liefern deshalb `warning`.
- `data/eos_v2.db` ist readonly und Smoke meldet `readonly_database`.

## Erwartete Abschlussausgabe

Der Abschlussbericht soll CLI-, Cron-, Telekom-, Test- und Push/PR-Status getrennt ausweisen:

- Runtime Doctor hinzugefügt: ja/nein
- CLI Smoke hinzugefügt: ja/nein
- Cron Smoke hinzugefügt: ja/nein
- Telekom-Paket gefunden: ja/nein
- einzelne CLI-Kommandostatus
- Tests und globale Tests
- Secrets gedruckt: nein
- Code geändert: ja/nein
- Push/PR erstellt: ja/nein
- Blocking Risks und nächster empfohlener Schritt
