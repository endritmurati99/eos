# EOS Gmail Synthetic Test Corpus v1

Status: implemented as synthetic classifier foundation

## Purpose

This package builds the first deterministic EOS mail intelligence layer without Gmail API access, OAuth scopes, real mailbox reads, or personal mail data.

It supports dry-run classification of bounded mail metadata and excerpts:

- operational action detection
- newsletter separation
- conservative money, security, legal, and health handling
- phishing, spam, and unknown-sender review flags
- synthetic regression tests for expected labels and safety invariants

## Contracts

Input model: `MailInput`

- `message_id: str | None`
- `thread_id: str | None`
- `sender: str`
- `subject: str`
- `snippet: str`
- `body_excerpt: str | None`
- `headers: dict[str, str]`

Output model: `MailClassification`

- `categories: list[str]`
- `priority: str`
- `requires_reply: bool`
- `safe_to_archive: bool`
- `confidence: float`
- `reason: str`
- `risk_flags: list[str]`

No full raw mail body, attachment content, OAuth token, Gmail scope, label write, archive, delete, send, unsubscribe, CLI integration, or persistence layer is part of this implementation.

## Rules

The classifier is deterministic and rule based. It uses normalized sender, subject, snippet, body excerpt, and headers only.

Rule groups cover:

- newsletter detection through `List-Unsubscribe`
- newsletter signal quality
- invoice, receipt, banking, credit card, tax, and subscription detection
- login alert, password reset, OTP, suspicious security, phishing, and spam detection
- reply/action cues
- work, university, personal, travel, shopping, health, and legal context
- unknown sender fallback

Safety defaults:

- Banking, credit card, tax, security, legal, health, phishing, spam, and unknown-sender cases are never archive-safe.
- `_EOS/Action Required` and `_EOS/Review Needed` are also never archive-safe.
- Newsletter cases are archive-safe only when `List-Unsubscribe` exists, no reply/action cue exists, no sensitive/risk category exists, and confidence is at least `0.95`.
- High-signal newsletters are retained for attention and are not archive-safe by default.
- Low confidence and risky cases receive `_EOS/Review Needed`.
- Classification confidence is bounded to `0.0..1.0`; direct `MailClassification` construction rejects out-of-range confidence.

Confidence bands:

- `>= 0.95`: strong deterministic signal
- `0.80-0.95`: useful suggestion, still conservative for sensitive mail
- `0.60-0.80`: review needed
- `< 0.60`: review needed

## Synthetic Corpus

The corpus lives in `tests/fixtures/mail_synthetic/` and contains 25 synthetic cases:

- `newsletter_high_signal`
- `newsletter_normal`
- `newsletter_low_signal`
- `newsletter_unsubscribe_candidate`
- `banking_info`
- `credit_card_alert`
- `invoice`
- `receipt`
- `tax`
- `subscription`
- `security_login_alert`
- `security_password_reset`
- `security_otp`
- `phishing_suspected`
- `spam_review`
- `unknown_sender`
- `personal_reply_required`
- `work_reply_required`
- `university_important`
- `calendar_related`
- `task_related`
- `legal`
- `shopping_delivery`
- `travel_booking`
- `health_appointment`

Fixtures use synthetic sender domains and synthetic message IDs only. They intentionally omit real names, real banking data, OTP values, password-reset links, login links, personal mailbox content, and Gmail API payloads.

## Hardening Validation

The fixture corpus remains at 25 JSON cases. Additional hardening is covered by direct unit tests for:

- newsletter plus banking statement
- newsletter plus reply request
- high-signal research newsletter retention
- phishing with security language and fake account-verification sender
- legal notice, contract, and Mahnung with newsletter header
- OTP, verification code, one-time password, and 2FA handling
- weak unknown-sender fallback
- confidence bounds
- hard no-archive category invariants
- generic reasons that do not echo OTP values, reset links, or raw sensitive snippets

No Gmail API, OAuth, label write, archive, delete, send, unsubscribe, CLI integration, or database persistence is introduced by this hardening pass.

## Verification

Run from the EOS workspace root:

```bash
python3 -m pytest tests/eos_mail/test_mail_classifier.py
python3 -m pytest
for f in tests/verify_*.py; do python3 "$f"; done
python3 -m src.eos_cli --help
git diff --check
```

If a host provides `python` instead of `python3`, the commands can be adapted. On the current workspace host, `python3` is the available interpreter.
