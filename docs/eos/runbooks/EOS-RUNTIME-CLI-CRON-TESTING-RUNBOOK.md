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

Die Smoke-Kommandos nach `--help` sind bewusst mit `|| true` abgesichert. Der Smoke soll Fehler sichtbar machen, nicht beim ersten Environment-Problem abbrechen.

Das Skript setzt automatisch einen temporären `EOS_DB_PATH`, wenn kein Wert vorhanden ist. Dadurch verändern Smoke-Läufe keine getrackte lokale Datenbank. Die Ausgabe maskiert Telegram-Ziele und offensichtliche Token-/Secret-Felder. Dry-Run-Kommandos können trotzdem echte Kalender-/Task-Inhalte enthalten; externe Berichte sollen deshalb nur Statuswerte und Fehlerklassen übernehmen.

## Cron/Systemd testen

Standardprüfung:

```bash
bash scripts/run_eos_cron_smoke.sh
```

Das Skript listet `ops/` Systemd-Dateien, führt `cron-audit` aus und fragt Systemd-Timer ab, falls `systemctl` verfügbar ist. In Container- oder CI-Umgebungen kann `systemctl` installiert sein, aber ohne laufenden Systemd-Daemon fehlschlagen. Das ist ein Environment-Problem, kein direkter EOS-Codefehler.

Auch dieses Skript setzt einen temporären `EOS_DB_PATH` und maskiert Telegram-Ziele sowie offensichtliche Secret-Felder.

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
