# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)

"""FV-108 XSS pass: put script-like text into every text input, then look at every
place it is shown (header, Friends, friends going, chat, restored history, Profile).
Fails if any script runs (alert dialog, a global flag) or markup becomes real elements."""

import re

from playwright.sync_api import expect, sync_playwright

from common import BASE, PROBLEMS, SHOTS, finish, go_to, launch, log_in, log_out, sql, watch

PAYLOADS = [
    "<img src=x onerror=\"window.__xss=1;alert(1)\">",
    "<script>window.__xss=1</script>",
    "\"><svg onload=\"window.__xss=1\">",
    "javascript:window.__xss=1",
    "{{constructor.constructor('window.__xss=1')()}}",
]
NAME = PAYLOADS[0][:100]


def guard(page, label):
    page.on("dialog", lambda d: (PROBLEMS.append(f"[{label}] script ran: dialog {d.message!r}"), d.dismiss()))


def assert_clean(page, label):
    if page.evaluate("window.__xss === 1"):
        PROBLEMS.append(f"[{label}] script ran (window.__xss set)")
    injected = page.evaluate("""() => [...document.querySelectorAll('img[src="x"], svg[onload], script:not([type=module]):not([src])')]
        .map(el => el.outerHTML.slice(0, 80))""")
    if injected:
        PROBLEMS.append(f"[{label}] markup became elements: {injected}")


with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    watch(page, "xss")
    guard(page, "xss")
    page.goto(BASE)

    # Registration form: payload display name (usernames are restricted to safe characters).
    import secrets
    users = []
    for prefix in ("xa", "xb"):
        username = f"{prefix}_{secrets.token_hex(3)}"
        dialog = page.get_by_role("dialog")
        dialog.get_by_role("button", name=re.compile("^Register")).click()
        dialog.get_by_label("Username").fill(username)
        dialog.get_by_label("Display name").fill(NAME)
        dialog.get_by_label("Email").fill(f"{username}@example.com")
        dialog.get_by_label("Password").fill("browser test password")
        dialog.get_by_label("Music").check()
        dialog.get_by_role("button", name="Create account").click()
        expect(dialog.get_by_role("status")).to_contain_text("Account created")
        users.append({"username": username, "password": "browser test password"})
    # A username with markup is rejected by the server.
    bad = page.request.post(f"{BASE}/api/auth/register", data={
        "username": "<b>x</b>", "display_name": "x", "email": "x@example.com",
        "password": "browser test password", "activity_preferences": ["Music"]})
    assert bad.status == 422, bad.status

    a, b = users
    log_in(page, a)
    expect(page.locator(".account-menu strong")).to_have_text(NAME)
    assert_clean(page, "header")

    # Chat requests (each payload), then the restored history after signing in again.
    for payload in PAYLOADS:
        page.get_by_label("Your request").fill(payload)
        page.get_by_role("button", name="Send", exact=True).click()
        expect(page.locator(".chat-message.from-user").last).to_have_text(re.compile(re.escape(payload[:20])))
    page.get_by_label("Your request").fill("music near " + PAYLOADS[1])
    page.get_by_role("button", name="Send", exact=True).click()
    page.wait_for_timeout(500)
    assert_clean(page, "chat")
    log_out(page)
    log_in(page, a)
    expect(page.locator(".chat-message.from-user")).to_have_count(len(PAYLOADS) + 1)
    assert_clean(page, "restored history")

    # Friends search (payload as the query), then follow each other with payload names shown.
    go_to(page, "Friends")
    page.get_by_label("Username").fill(PAYLOADS[2][:50])
    page.get_by_role("button", name="Search").click()
    page.wait_for_timeout(300)
    assert_clean(page, "friends search")
    page.get_by_label("Username").fill(b["username"])
    page.get_by_role("button", name="Search").click()
    page.get_by_role("button", name=f"Follow @{b['username']}").click()
    a_card_event = sql("SELECT 1")  # keep the DB connection warm
    log_out(page)
    log_in(page, b)
    go_to(page, "Friends")
    page.get_by_role("button", name=f"Follow back @{a['username']}").first.click()
    expect(page.get_by_role("button", name=f"See plans of @{a['username']}").first).to_be_visible()
    go_to(page, "Events")
    first = page.locator("#events article.event-card").first
    first.get_by_role("button", name=re.compile("^Save to My Plans")).click()
    log_out(page)
    log_in(page, a)
    go_to(page, "Friends")
    page.get_by_role("button", name=f"See plans of @{b['username']}").first.click()
    expect(page.get_by_role("region", name=re.compile("upcoming plans"))).to_be_visible()
    assert_clean(page, "friends lists and friend plans")
    go_to(page, "Events")
    page.locator("#events article.event-card").first.get_by_role("button", name="View details").click()
    expect(page.locator("#events .friends-going")).to_contain_text("is going")
    assert_clean(page, "friends going")

    # Profile: payloads in the display name field.
    go_to(page, "Profile")
    for payload in PAYLOADS[1:]:
        page.get_by_label("Display name").fill(payload)
        page.get_by_role("button", name="Save changes").click()
        expect(page.locator(".account-menu strong")).to_have_text(payload)
    assert_clean(page, "profile")
    page.screenshot(path=SHOTS / "xss-profile.png", full_page=True)

    # Security headers / cookie flags as the browser sees them.
    cookies = [c for c in ctx.cookies() if c["name"] == "session"]
    assert cookies and cookies[0]["httpOnly"] and cookies[0]["sameSite"] == "Lax" and cookies[0]["path"] == "/api", cookies
    assert page.evaluate("document.cookie").find("session=") == -1
    browser.close()

for user in users:
    sql(f"DELETE FROM users WHERE username = '{user['username']}'")
finish()
