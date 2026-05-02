from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

CONFIRMATION_TTL_MINUTES = 30


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expires_utc() -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=CONFIRMATION_TTL_MINUTES)).isoformat()


class ConfirmationService:
    @staticmethod
    def create(
        intake_result: Any,
        *,
        user_id: str = "cli",
        source: str = "cli",
        connection: Any,
    ) -> dict[str, Any]:
        cid = str(uuid.uuid4())
        now = _now_utc()
        expires = _expires_utc()
        entities_json = json.dumps(intake_result.entities) if intake_result.entities else None
        question = intake_result.confirmation_question or "Bitte bestätige deine Eingabe."

        connection.execute(
            """
            INSERT INTO pending_confirmations
                (id, created_at_utc, expires_at_utc, user_id, source, original_text,
                 parsed_intent, parsed_entities_json, confirmation_question, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (cid, now, expires, user_id, source, intake_result.raw_input,
             intake_result.intent, entities_json, question),
        )
        connection.commit()
        return {
            "id": cid,
            "status": "pending",
            "confirmation_question": question,
            "expires_at_utc": expires,
        }

    @staticmethod
    def list_pending(user_id: str, *, connection: Any) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT * FROM pending_confirmations
            WHERE user_id = ? AND status = 'pending'
              AND expires_at_utc > ?
            ORDER BY created_at_utc DESC
            """,
            (user_id, _now_utc()),
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def resolve_with_text(
        confirmation_id: str,
        resolution_text: str,
        *,
        connection: Any,
    ) -> dict[str, Any]:
        now = _now_utc()
        resolution = json.dumps({"resolution_text": resolution_text})
        connection.execute(
            """
            UPDATE pending_confirmations
            SET status = 'resolved', resolved_at_utc = ?, resolution_json = ?
            WHERE id = ?
            """,
            (now, resolution, confirmation_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM pending_confirmations WHERE id = ?", (confirmation_id,)
        ).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def expire_all(*, connection: Any) -> int:
        now = _now_utc()
        cursor = connection.execute(
            """
            UPDATE pending_confirmations
            SET status = 'expired'
            WHERE status = 'pending' AND expires_at_utc <= ?
            """,
            (now,),
        )
        connection.commit()
        return cursor.rowcount

    @staticmethod
    def cancel(confirmation_id: str, *, connection: Any) -> dict[str, Any]:
        now = _now_utc()
        connection.execute(
            "UPDATE pending_confirmations SET status = 'cancelled', resolved_at_utc = ? WHERE id = ?",
            (now, confirmation_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM pending_confirmations WHERE id = ?", (confirmation_id,)
        ).fetchone()
        return dict(row) if row else {}

    @staticmethod
    def get(confirmation_id: str, *, connection: Any) -> dict[str, Any] | None:
        row = connection.execute(
            "SELECT * FROM pending_confirmations WHERE id = ?", (confirmation_id,)
        ).fetchone()
        return dict(row) if row else None
