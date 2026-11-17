# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)

"""Shared helpers for browser checks against the running project (localhost:3000)."""

import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import Page, expect

BASE = "http://localhost:3000"
SHOTS = Path(__file__).resolve().parent / "shots"
SHOTS.mkdir(exist_ok=True)
CODE = Path(__file__).resolve().parents[1]  # the code/ folder

PROBLEMS: list[str] = []


def watch(page: Page, label: str) -> None:
    """Record console errors, page errors, and failed (5xx) API answers."""
    page.on("console", lambda msg: msg.type == "error" and not _expected(msg.text)
            and PROBLEMS.append(f"[{label}] console: {msg.text}"))
    page.on("pageerror", lambda err: PROBLEMS.append(f"[{label}] page error: {err}"))
    page.on("response", lambda r: r.status >= 500 and PROBLEMS.append(f"[{label}] {r.status} {r.url}"))


def _expected(text: str) -> bool:
    # The browser logs every non-2xx fetch; 401 before login and deliberate 404/409 are expected.
    return bool(re.search(r"status of (401|404|409)", text))


def register_via_api(page: Page, prefix: str, preferences=("Music",)) -> dict:
    username = f"{prefix}_{secrets.token_hex(3)}"
    account = {
        "username": username, "display_name": prefix.title(), "email": f"{username}@example.com",
        "password": "browser test password", "activity_preferences": list(preferences),
    }
    response = page.request.post(f"{BASE}/api/auth/register", data=account)
    assert response.status == 201, response.text()
    return account | {"id": response.json()["id"]}


def log_in(page: Page, account: dict) -> None:
    dialog = page.get_by_role("dialog")
    expect(dialog).to_be_visible()
    dialog.get_by_role("button", name=re.compile("^Log in")).click()
    dialog.get_by_label("Username").fill(account["username"])
    dialog.get_by_label("Password").fill(account["password"])
    dialog.get_by_role("button", name="Log In", exact=True).click()
    expect(page.get_by_text("Signed in as")).to_be_visible()
    expect(dialog).to_be_hidden()


def log_out(page: Page) -> None:
    page.get_by_role("button", name="Log Out").click()
    expect(page.get_by_role("dialog")).to_be_visible()


def go_to(page: Page, name: str) -> None:
    page.get_by_role("navigation", name="Main menu").get_by_role("button", name=name, exact=True).click()


def sql(query: str) -> str:
    result = subprocess.run(
        ["docker", "compose", "--project-directory", str(CODE / "User_Database"), "exec", "-T", "database",
         "psql", "-U", "movie_admin", "-d", "movie_users", "-tAc", query],
        capture_output=True, text=True, check=True)
    return result.stdout.strip()


def no_horizontal_scroll(page: Page, label: str) -> None:
    width = page.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
    assert width[0] <= width[1], f"{label}: page scrolls sideways ({width[0]} > {width[1]})"


def small_targets(page: Page, selector: str) -> list[str]:
    """Visible buttons shorter than 44px (the FV-110 touch target rule)."""
    return page.eval_on_selector_all(selector, """els => els
        .filter(el => el.offsetParent !== null && el.getBoundingClientRect().height < 44)
        .map(el => `${el.textContent.trim()} (${Math.round(el.getBoundingClientRect().height)}px)`)""")


def finish() -> None:
    if PROBLEMS:
        print("PROBLEMS:\n" + "\n".join(PROBLEMS))
        sys.exit(1)
    print("ALL BROWSER CHECKS PASSED")


def launch(p):
    """Playwright's own Chromium, or another Chrome/Chromium set in CHROME_PATH."""
    path = os.environ.get("CHROME_PATH")
    return p.chromium.launch(executable_path=path) if path else p.chromium.launch()
