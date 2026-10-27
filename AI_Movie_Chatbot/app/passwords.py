# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~90%
# AI-Assisted Areas: scrypt hashing, constant-time verification, dummy hash
# Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
# Notes/Verification: tests/test_auth.py, tests/live_auth.py; reviewed against the OWASP Password Storage Cheat Sheet

"""Password hashing with the standard library's scrypt; no extra dependency."""

import base64
import hashlib
import hmac
import secrets

# 16 MiB of memory per hash: slow for attackers, fast enough for a login request.
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1
SALT_BYTES, KEY_BYTES = 16, 32


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p,
                          maxmem=64 * 1024 * 1024, dklen=KEY_BYTES)


# AI-ASSISTED: YES
# Tool: Claude Code (Claude Opus)
# Prompt Summary: "Add real register and log in (backend API, users in the database), make log out reopen the pop-up, serve the sample events from the backend, fix event time ordering, and make sure it all works"
# AI Contribution: initial implementation (~90%)
# Modifications:
#  - Daniel chose the standard-library scrypt (no new dependency) and reviewed the parameters
# Verification:
#  - tests/test_auth.py (salted hash verifies; missing or malformed hash never matches)
#  - manual login in the browser
# Confidence: High
def hash_password(password: str) -> str:
    """Return 'scrypt$n$r$p$salt$key'; each hash has its own random salt."""
    salt = secrets.token_bytes(SALT_BYTES)
    key = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    encode = lambda raw: base64.b64encode(raw).decode("ascii")
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${encode(salt)}${encode(key)}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Compare in constant time; missing or malformed hashes never match."""
    try:
        algorithm, n, r, p, salt, key = (stored_hash or "").split("$")
        if algorithm != "scrypt":
            return False
        expected = base64.b64decode(key, validate=True)
        actual = _scrypt(password, base64.b64decode(salt, validate=True), int(n), int(r), int(p))
    except ValueError:
        return False
    return hmac.compare_digest(actual, expected)


# Checked when a username does not exist, so both failures take similar time.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))
