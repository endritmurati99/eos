# Feature Requests

Capabilities requested by the user.

---

## [FEAT-20260424-001] tts_fallback_chain

**Logged**: 2026-04-24T06:28:05+02:00
**Priority**: medium
**Status**: partially_applied
**Area**: infra

### Requested Capability
Mehrere funktionierende Audio-Ausgabewege nacheinander prüfen und bei Ausfall automatisch auf einen anderen TTS-Weg wechseln.

### User Context
Endrit möchte tägliche Briefings auch als Audio in Telegram und erwartet, dass bei Ausfällen andere verfügbare Wege genutzt werden.

### Complexity Estimate
medium

### Suggested Implementation
Fallback-Kette für TTS definieren: primärer Provider, sekundärer Provider und optional lokaler CLI-Fallback mit Audio-Umwandlung für Telegram.

### Implementation Note
2026-04-28: Eine kleine TTS-Pipeline mit lokalem Piper-WAV-Pfad und strukturierten Fehlerresultaten wurde angelegt. Telegram-Versand und optionale Transkodierung bleiben separate naechste Schritte.

### Metadata
- Frequency: recurring
- Related Features: tts

---
