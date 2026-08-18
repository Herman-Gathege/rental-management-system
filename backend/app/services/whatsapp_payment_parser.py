"""WhatsApp payment-evidence parser (Sprint 7 WhatsApp integration).

Conservative parser for free-form tenant WhatsApp messages that may contain
payment evidence.  Produces:

    is_payment_evidence  — whether the message looks like a payment confirmation
    reference            — extracted payment reference (if any)
    amount               — extracted amount in KES (if any)
    confidence           — high | medium | low | none
    evidence             — list of human-readable reasons for the classification

Design goals:
  - Do not invent a reference from every alphanumeric token.
  - Preserve the original raw message as evidence; never mutate it.
  - Amount extraction is deliberately strict — a missed amount is better
    than a fabricated one.
  - Detection is additive: a false positive (treating a normal message as
    payment evidence) is preferable to silently dropping a real payment, but
    ordinary tenant conversations should not flood the review queue.
"""

from __future__ import annotations

import re
from typing import Any


# ── Detection keywords (case-insensitive) ────────────────────────────────────
# A message is considered payment evidence if it contains one of these
# in a meaningful context.  We combine keyword hits with structural patterns
# to avoid flagging "RENT IS DUE" or "I WILL PAY LATER".
_DETECTION_KEYWORDS = re.compile(
    r"\b(MPESA|PESA|PAYMENT|PAID|RENT|DEPOSIT|TRANSACTION|BANK|CASH)\b",
    re.IGNORECASE,
)

# Known structural patterns for standalone payment confirmations:
#   <reference> <phone> - <name>
#   <reference> <masked_phone> - <name>
_STANDALONE_REF_PATTERN = re.compile(
    r"^\s*([A-Z0-9]{6,14})\s+((?:\+?\d{6,15})|(?:\d+\*+\d+))\s*-\s*",
    re.IGNORECASE,
)

# M-Pesa standard format:
#   MPESA TO ACC <account> <reference> TIMESTAMP: <ts> TO <account>
_MPESA_ACC_PATTERN = re.compile(
    r"MPESA\s+TO\s+ACC\s+\d+\s+([A-Z0-9]+)\s+TIMESTAMP",
    re.IGNORECASE,
)

# PESA keyword followed by a long hex-like reference:
#   PESA <longhex> ...
_PESA_REF_PATTERN = re.compile(
    r"^\s*PESA\s+([A-F0-9]{16,64})\b",
    re.IGNORECASE,
)

# Amount after the keyword DEPOSIT (with optional preceding number):
#   ... DEPOSIT <amount>
# We are strict: amount must look like a decimal number.
# Put \d+ before the grouped alternative so "DEPOSIT 15000" captures all 5 digits
# rather than stopping at the first 1-3 digit chunk.
_DEPOSIT_AMOUNT_PATTERN = re.compile(
    r"DEPOSIT\s+(\d+(?:,\d{3})*|\d{1,3}(?:,\d{3})*)(?:\.\d+)?",
    re.IGNORECASE,
)

# Standalone amount that is NOT part of a phone / timestamp / account number:
# Requires word boundaries and at least 4 digits (to avoid matching short
# transaction IDs or dates).  Used as a last-resort fallback only when a
# reference is also present.
_STANDALONE_AMOUNT_PATTERN = re.compile(
    r"(?<!\d)(\d{4,}(?:,\d{3})*|\d{4,})(?:\.\d+)?(?!\d)",
)

# Date-like tokens that should NOT be interpreted as amounts.
_DATE_LIKE_PATTERN = re.compile(
    r"^\d{6,8}$|^\d{2}/\d{2}/\d{2,4}$|^\d{4}-\d{2}-\d{2}$"
)


def _norm_phone(raw: str) -> str | None:
    """Reduce any phone format to its last 9 local digits for matching."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return None
    return digits[-9:] if len(digits) >= 9 else digits


def _looks_like_date(token: str) -> bool:
    if _DATE_LIKE_PATTERN.match(token.strip()):
        return True
    # Standalone 4-digit year (e.g. "2026" in "RENT FOR MAY 2026").
    if re.match(r"^\d{4}$", token.strip()):
        try:
            year = int(token.strip())
            return 1900 <= year <= 2100
        except ValueError:
            pass
    return False


def parse_whatsapp_payment(body: str) -> dict[str, Any]:
    """Parse a WhatsApp message body for payment evidence.

    Parameters
    ----------
    body:
        Raw message text from Meta.

    Returns
    -------
    dict with keys:
        is_payment_evidence (bool)
        reference (str | None)
        amount (float | None)
        confidence (str)
        evidence (list[str])
    """
    if not body or not body.strip():
        return {
            "is_payment_evidence": False,
            "reference": None,
            "amount": None,
            "confidence": "none",
            "evidence": ["empty message"],
        }

    body = body.strip()
    evidence: list[str] = []
    ref: str | None = None
    amount: float | None = None
    confidence = "none"

    # ── Step 1: detection ────────────────────────────────────────────────────
    is_payment_evidence = False

    # Structural patterns are strong signals regardless of keywords.
    if _MPESA_ACC_PATTERN.search(body):
        is_payment_evidence = True
        evidence.append("mpesa_acc_format")

    if _PESA_REF_PATTERN.search(body):
        is_payment_evidence = True
        evidence.append("pesa_keyword_with_longhex")

    if _STANDALONE_REF_PATTERN.search(body):
        is_payment_evidence = True
        evidence.append("standalone_ref_phone_name_format")

    # Keyword detection — only count if there is ALSO a structural hint
    # (reference-like token, amount-like token, or ACC keyword).
    keyword_hits = _DETECTION_KEYWORDS.findall(body)
    if keyword_hits:
        evidence.append(f"keywords:{','.join(set(k.upper() for k in keyword_hits))}")
        # If we already have a structural signal, keywords boost confidence.
        # If not, strong payment-specific keywords alone still count as evidence,
        # especially when accompanied by numeric context (account numbers,
        # timestamps, amounts).
        if not is_payment_evidence:
            strong_keywords = {"MPESA", "PESA", "CASH", "DEPOSIT", "TRANSACTION", "BANK"}
            has_strong = bool(set(k.upper() for k in keyword_hits) & strong_keywords)
            has_numeric_context = bool(re.search(r'\d', body))
            if has_strong and has_numeric_context:
                is_payment_evidence = True
                evidence.append("payment_keywords_with_numeric_context")
            elif re.search(r"\bMPESA\b|\bPESA\b", body, re.IGNORECASE):
                is_payment_evidence = True
                evidence.append("mpesa_or_pesa_keyword_alone")

    # If nothing flagged it, bail early.
    if not is_payment_evidence:
        return {
            "is_payment_evidence": False,
            "reference": None,
            "amount": None,
            "confidence": "none",
            "evidence": evidence,
        }

    # ── Step 2: reference extraction ────────────────────────────────────────
    # Priority order: most reliable patterns first.

    if m := _MPESA_ACC_PATTERN.search(body):
        ref = m.group(1)
        evidence.append("reference_from_mpesa_acc")

    elif m := _STANDALONE_REF_PATTERN.search(body):
        ref = m.group(1)
        evidence.append("reference_from_standalone_format")

    elif m := _PESA_REF_PATTERN.search(body):
        ref = m.group(1)
        evidence.append("reference_from_pesa_longhex")

    if ref:
        # M-Pesa ACC and PESA longhex patterns are structurally strong enough
        # to count as high confidence even without an extracted amount.
        if _MPESA_ACC_PATTERN.search(body) or _PESA_REF_PATTERN.search(body):
            confidence = "high"
        else:
            confidence = "medium"  # will be upgraded to high if amount also found
    else:
        # No confident reference — still payment evidence but low confidence.
        confidence = "low"
        evidence.append("no_confident_reference")

    # ── Step 3: amount extraction ───────────────────────────────────────────
    # Only extract amount if we also have a reference (require both for medium+).
    # Exception: DEPOSIT keyword messages may have an amount without a reference.
    has_deposit_keyword = bool(re.search(r'\bDEPOSIT\b', body, re.IGNORECASE))
    if ref or has_deposit_keyword:
        # Try DEPOSIT <amount> first (common in cash-deposit messages).
        if m := _DEPOSIT_AMOUNT_PATTERN.search(body):
            candidate = m.group(1).replace(",", "")
            try:
                val = float(candidate)
                # Sanity: reject unreasonably large amounts (> 10M KES).
                if 1 <= val <= 10_000_000:
                    amount = val
                    evidence.append("amount_from_deposit_keyword")
            except ValueError:
                pass

        # Fallback: standalone large number that doesn't look like a date
        # and isn't part of the reference or a phone/account number.
        if amount is None and ref:
            for m in _STANDALONE_AMOUNT_PATTERN.finditer(body):
                candidate = m.group(1).replace(",", "")
                if _looks_like_date(candidate):
                    continue
                # Skip exact reference match.
                if candidate.lower() == ref.lower():
                    continue
                # Skip if the candidate is part of a longer digit string in the
                # original body (e.g. "25479****032" would yield "25479").
                start, end = m.span(1)
                if (start > 0 and body[start - 1].isdigit()) or \
                   (end < len(body) and body[end].isdigit()):
                    continue
                # Skip if the match is embedded in a masked phone / account token
                # (e.g. "25479****032" would yield candidate "25479" — reject it).
                if start > 0 and body[start - 1] == "*":
                    continue
                if end < len(body) and body[end] == "*":
                    continue
                # Skip if the candidate is part of a larger token that contains
                # letters (e.g. "DE4116FA5C6E4B52AD2365438BB530B1" would yield
                # candidate "4116" — reject it because it's a hex fragment).
                token_start = start
                while token_start > 0 and body[token_start - 1].isalnum():
                    token_start -= 1
                token_end = end
                while token_end < len(body) and body[token_end].isalnum():
                    token_end += 1
                token = body[token_start:token_end]
                if any(c.isalpha() for c in token):
                    continue
                # Sanity: reject unreasonably large amounts (> 10M KES).
                try:
                    val = float(candidate)
                    if val > 10_000_000:
                        continue
                    if val >= 1:
                        amount = val
                        evidence.append("amount_from_standalone_number")
                        break
                except ValueError:
                    continue

    # ── Step 4: final confidence calibration ────────────────────────────────
    # Amount presence can upgrade medium → high, but never downgrade.
    if amount and confidence != "high":
        confidence = "high"
    # else: confidence remains "low" (no ref) or "none" (not payment evidence)

    return {
        "is_payment_evidence": is_payment_evidence,
        "reference": ref,
        "amount": amount,
        "confidence": confidence,
        "evidence": evidence,
    }
