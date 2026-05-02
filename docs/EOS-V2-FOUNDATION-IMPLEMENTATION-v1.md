# EOS V2 Foundation Implementation v1

## Zweck
Dieses Dokument beschreibt den ersten technischen Unterbau fuer EOS V2 nach dem Spec-Freeze.
Step 1 implementiert State, Google-Tasks-Gateway, `evening_reset`-Logik und ein Verifikationsskript.

Alle in `EOS-V2-IMPLEMENTATION-STEP-1.md` geforderten Eingabedokumente waren vor Start vorhanden.

## Angelegte oder aktualisierte Dateien
- `src/database/models.py`
  - SQLite-Initialisierung, Pfadaufloesung, Tabellenanlage fuer `job_runs`, `daily_evaluations` und `task_snapshots`
- `src/database/__init__.py`
  - Exporte fuer `init_db`, `resolve_db_path`, `connect_db`
- `src/gateways/google_tasks.py`
  - `TaskGateway` als `gog`-basierter Step-1-Adapter fuer Read, Create, Complete und headless Auth-Bootstrap
- `src/jobs/evening_reset.py`
  - Dry-Run-faehige `evening_reset`-Logik mit Kalender-/Task-Read, Minimal-Coaching, Snapshot-Persistenz und Idempotenz
- `tests/verify_v2_foundation.py`
  - Plain-Python-Smoke-Test fuer DB, Gateway und `evening_reset`

## Verwendete ENV-Variablen
- `EOS_DB_PATH`
  - optionaler SQLite-Pfad
  - Default: `./data/eos_v2.db`
- `EOS_GOG_BIN`
  - bevorzugter Pfad zum `gog`-Binary
  - noetig, wenn `gog` nicht auf `PATH` liegt
- `EOS_GOOGLE_ACCOUNT`
  - optionale Google-Account-Mail fuer `gog`
  - faellt sonst auf `integrations/calendar-source.json.account` zurueck
- `EOS_GOOGLE_CREDENTIALS_PATH`
  - Pfad zum OAuth-Client-JSON fuer `gog auth credentials set`
- `EOS_GOOGLE_TOKEN_PATH`
  - isolierter `XDG_CONFIG_HOME`-Root fuer `gog`-Auth-State
  - wird nicht als rohes Token-JSON interpretiert
- `EOS_VERIFY_TASK_LIST`
  - optionale Liste fuer den Verifikations-Read
  - Default: `Inbox`

## Was in Step 1 direkt testbar ist
- DB-Bootstrap fuer die drei V2-Tabellen
- Smoke-Write nach SQLite
- `TaskGateway.get_auth_status()`
- `TaskGateway.get_open_tasks()`
- `TaskGateway.create_task()`
- `TaskGateway.complete_task()`
- `TaskGateway.prepare_headless_auth()`
- `TaskGateway.finalize_headless_auth()`
- `run_evening_reset(dry_run=True, allow_stub_calendar=True)`
- `tests/verify_v2_foundation.py`

## Was bereits live nutzbar ist
- SQLite als Derived-State-Basis
- `evening_reset` als Output-Generator ohne Telegram-Send
- `gog`-basierter Google-Tasks-Zugriff, sobald Credentials und Tokens sauber vorhanden sind

## Was nur vorbereitet ist
- produktive Google-Tasks-Auth
- produktiver Live-Calendar-Read fuer `evening_reset`
- echter Telegram-Send
- Scheduler-/Timer-Aktivierung
- Weekly Review / `weekly_sync`

## Wichtige Step-1-Regeln
- Keine Secrets werden in Code oder Markdown gespeichert.
- Keine `systemd`-, `cron`- oder Legacy-Job-Aenderung wird vorgenommen.
- SQLite bleibt Derived State und ersetzt keine Primaerquelle.
- Wenn Tasks fehlen, bleibt `evening_reset` im Dry-Run dennoch grundsaetzlich erzeugbar.
- `generated` ist ein temporaerer Step-1-`run_status`, bis echte Delivery-Semantik spaeter folgt.

## Aktuell verifizierte Runtime-Fakten
- `python3` ist vorhanden
- `sqlite3` ist vorhanden
- `requests` und `jinja2` sind vorhanden
- Google Python API Libraries sind aktuell nicht installiert
- `gog` ist im aktuellen Umfeld vorhanden, aber nicht zwingend auf `PATH`
- `gog auth list` meldete waehrend der Planung `No tokens stored`
- `gog auth credentials list` meldete waehrend der Planung `No OAuth client credentials stored`

## Risiken und offene Punkte
- Ohne `EOS_GOG_BIN` oder `PATH`-Eintrag ist `gog` nicht automatisch aufloesbar
- Ohne OAuth-Client und Refresh-Token bleibt das Gateway bei `config_missing` oder `auth_required`
- `evening_reset` nutzt in Dry-Run/Verifikation einen klar markierten Stub-Fallback aus `data/calendar.json`, aber nicht als produktive Wahrheit
- `job_runs` ist in Step 1 bewusst minimal und speichert pro Idempotenz-Key nur den letzten relevanten Zustand
- Telegram-Delivery, `sent`-Semantik und produktive Retry-Strategie bleiben fuer spaetere Schritte offen
