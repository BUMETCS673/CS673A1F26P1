# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)

"""FV-95 browser check: two real accounts, the real API and database, desktop and phone."""

import re

from playwright.sync_api import expect, sync_playwright

from common import (BASE, launch, SHOTS, finish, go_to, log_in, log_out, no_horizontal_scroll,
                    register_via_api, small_targets, sql, watch)

with sync_playwright() as p:
    browser = launch(p)

    # ---------- Desktop, account 1 (registered through the UI, like a person) ----------
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    watch(page, "desktop")
    page.goto(BASE)
    dialog = page.get_by_role("dialog")
    dialog.get_by_role("button", name=re.compile("^Register")).click()
    import secrets
    alex = {"username": f"alex_{secrets.token_hex(3)}", "password": "browser test password"}
    dialog.get_by_label("Username").fill(alex["username"])
    dialog.get_by_label("Display name").fill("Alex")
    dialog.get_by_label("Email").fill(f"{alex['username']}@example.com")
    dialog.get_by_label("Password").fill(alex["password"])
    dialog.get_by_label("Music").check()
    dialog.get_by_role("button", name="Create account").click()
    expect(dialog.get_by_role("status")).to_contain_text("Account created")
    log_in(page, alex)
    alex_id = sql(f"SELECT id FROM users WHERE username = '{alex['username']}'")

    events = page.locator("#events")
    cards = events.locator("article.event-card")
    expect(cards.first).to_be_visible()
    first_title = cards.nth(0).locator("h3").inner_text()
    second_title = cards.nth(1).locator("h3").inner_text()

    # Save from a card, with a fast double click: one row only.
    save = cards.nth(0).get_by_role("button", name=f"Save to My Plans: {first_title}")
    save.dblclick()
    expect(cards.nth(0).get_by_text("✓ In My Plans")).to_be_visible()
    assert sql(f"SELECT count(*) FROM user_plans WHERE user_id = {alex_id}") == "1"

    # Save from the details view, using only the keyboard.
    cards.nth(1).get_by_role("button", name="View details").click()
    details = events.locator(".panel", has=page.get_by_role("button", name="Close details"))
    expect(details.get_by_role("heading", name=second_title)).to_be_visible()
    details.get_by_role("button", name=f"Save to My Plans: {second_title}").focus()
    page.keyboard.press("Enter")
    expect(details.get_by_text("✓ In My Plans")).to_be_visible()
    # The card for the same event updates too.
    expect(cards.nth(1).get_by_text("✓ In My Plans")).to_be_visible()
    page.screenshot(path=SHOTS / "plans-1-events-saved.png", full_page=True)

    # My Plans shows both, grouped by Boston day.
    go_to(page, "My Plans")
    plans_page = page.locator("main.my-plans")
    expect(plans_page.get_by_role("heading", name=first_title)).to_be_visible()
    expect(plans_page.get_by_role("heading", name=second_title)).to_be_visible()
    day_headings = plans_page.locator(".plan-day-heading").all_inner_texts()
    assert day_headings and all(re.match(r"^\w+day, \w+ \d+, 2026$", h) for h in day_headings), day_headings
    page.screenshot(path=SHOTS / "plans-2-my-plans-desktop.png", full_page=True)

    # A reload keeps the session and the plans.
    page.reload()
    expect(page.get_by_text("Signed in as")).to_be_visible()
    go_to(page, "My Plans")
    expect(plans_page.locator("li.plan-item")).to_have_count(2)

    # View details from My Plans opens the Events page with that event.
    plans_page.get_by_role("button", name=f"View details: {second_title}").click()
    expect(events).to_be_visible()
    expect(details.get_by_role("heading", name=second_title)).to_be_visible()
    expect(details.get_by_text("✓ In My Plans")).to_be_visible()
    expect(page.get_by_role("button", name="Events", exact=True)).to_have_attribute("aria-current", "page")

    # Remove from My Plans; it disappears and stays removed after a reload.
    go_to(page, "My Plans")
    plans_page.get_by_role("button", name=f"Remove from My Plans: {first_title}").click()
    expect(plans_page.get_by_role("heading", name=first_title)).to_have_count(0)
    page.reload()
    go_to(page, "My Plans")
    expect(plans_page.locator("li.plan-item")).to_have_count(1)
    assert sql(f"SELECT event_id FROM user_plans WHERE user_id = {alex_id}") != ""

    # ---------- Second account in the same browser: nothing of Alex's shows ----------
    log_out(page)
    sam = register_via_api(page, "sam")
    log_in(page, sam)
    expect(page.locator("#events article.event-card").first).to_be_visible()
    go_to(page, "My Plans")
    expect(page.get_by_role("heading", name="No plans yet")).to_be_visible()
    # Sam's API calls cannot touch Alex's rows.
    page.request.delete(f"{BASE}/api/plans/{sql(f'SELECT event_id FROM user_plans WHERE user_id = {alex_id}')}")
    assert sql(f"SELECT count(*) FROM user_plans WHERE user_id = {alex_id}") == "1"
    page.get_by_role("button", name="Browse events").click()
    expect(events).to_be_visible()
    log_out(page)
    log_in(page, alex)
    go_to(page, "My Plans")
    expect(plans_page.get_by_role("heading", name=second_title)).to_be_visible()

    # Unknown and ended events through the real API.
    assert page.request.put(f"{BASE}/api/plans/no-such-event").status == 404
    assert page.request.put(f"{BASE}/api/plans/{'x' * 101}").status == 422
    context.close()

    # ---------- Phone size ----------
    phone = browser.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True)
    page = phone.new_page()
    watch(page, "phone")
    page.goto(BASE)
    log_in(page, alex)
    events = page.locator("#events")
    cards = events.locator("article.event-card")
    expect(cards.first).to_be_visible()
    cards.nth(2).get_by_role("button", name=re.compile("^Save to My Plans")).tap()
    expect(cards.nth(2).get_by_text("✓ In My Plans")).to_be_visible()
    no_horizontal_scroll(page, "phone events")
    page.screenshot(path=SHOTS / "plans-3-events-phone.png", full_page=True)
    go_to(page, "My Plans")
    expect(page.locator("li.plan-item")).to_have_count(2)
    no_horizontal_scroll(page, "phone My Plans")
    small = small_targets(page, "main.my-plans button")
    assert not small, f"buttons under 44px on phone: {small}"
    page.screenshot(path=SHOTS / "plans-4-my-plans-phone.png", full_page=True)
    phone.close()

    # ---------- Tablet size ----------
    tablet = browser.new_context(viewport={"width": 768, "height": 1024})
    page = tablet.new_page()
    watch(page, "tablet")
    page.goto(BASE)
    log_in(page, alex)
    go_to(page, "My Plans")
    expect(page.locator("li.plan-item")).to_have_count(2)
    no_horizontal_scroll(page, "tablet My Plans")
    page.screenshot(path=SHOTS / "plans-5-my-plans-tablet.png", full_page=True)
    tablet.close()

    browser.close()

# Clean up the test accounts (plans cascade).
sql(f"DELETE FROM users WHERE username IN ('{alex['username']}', '{sam['username']}')")
assert sql(f"SELECT count(*) FROM user_plans WHERE user_id = {alex_id}") == "0"
finish()
