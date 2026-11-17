# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)

"""FV-103 browser check: edit the profile like a person, with two real accounts."""

from playwright.sync_api import expect, sync_playwright

from common import (BASE, SHOTS, finish, go_to, launch, log_in, log_out, no_horizontal_scroll,
                    register_via_api, small_targets, sql, watch)

with sync_playwright() as p:
    browser = launch(p)
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    watch(page, "desktop")
    alex = register_via_api(page, "alex", preferences=("Music",))
    sam = register_via_api(page, "sam", preferences=("Food",))
    page.goto(BASE)
    log_in(page, alex)

    go_to(page, "Profile")
    expect(page.get_by_text(f"@{alex['username']}")).to_be_visible()
    name = page.get_by_label("Display name")
    expect(name).to_have_value("Alex")
    save = page.get_by_role("button", name="Save changes")
    expect(save).to_be_disabled()

    # Client-side checks, then a real save using only the keyboard for the checkboxes.
    name.fill("   ")
    save.click()
    expect(page.get_by_role("alert")).to_have_text("Display name is required.")
    expect(name).to_be_focused()
    name.fill("Alex Park")
    page.get_by_role("checkbox", name="Music").press("Space")  # unchecks the only preference
    save.click()
    expect(page.get_by_role("alert")).to_have_text("Choose at least one activity preference.")
    page.get_by_role("checkbox", name="Outdoors").press("Space")
    page.get_by_role("checkbox", name="Arts").press("Space")
    save.click()
    expect(page.get_by_role("status").filter(has_text="Profile saved.")).to_be_visible()
    expect(page.locator(".account-menu")).to_contain_text("Signed in as Alex Park")
    assert sql(f"SELECT display_name, activity_preferences FROM users WHERE id = {alex['id']}") == \
        "Alex Park|{Arts,Outdoors}"
    page.screenshot(path=SHOTS / "profile-1-saved-desktop.png", full_page=True)

    # Reload keeps the session and the change.
    page.reload()
    expect(page.locator(".account-menu")).to_contain_text("Signed in as Alex Park")
    go_to(page, "Profile")
    expect(page.get_by_role("checkbox", name="Outdoors")).to_be_checked()
    expect(page.get_by_role("checkbox", name="Music")).not_to_be_checked()

    # The browser cannot change username, email, or another account through the API.
    for body in ({"username": "hijack"}, {"email": "x@example.com"}, {"display_name": "Sam?", "id": sam["id"]}):
        assert page.request.patch(f"{BASE}/api/auth/me", data=body).status == 422, body
    assert sql(f"SELECT display_name FROM users WHERE id = {sam['id']}") == "Sam"

    # Markup in a display name is shown as text everywhere it appears.
    name = page.get_by_label("Display name")
    name.fill("<b>Bold</b> Alex")
    page.get_by_role("button", name="Save changes").click()
    expect(page.locator(".account-menu strong")).to_have_text("<b>Bold</b> Alex")
    assert page.locator(".account-menu b").count() == 0

    # Sam sees their own profile only.
    log_out(page)
    log_in(page, sam)
    go_to(page, "Profile")
    expect(page.get_by_label("Display name")).to_have_value("Sam")
    expect(page.get_by_role("checkbox", name="Food")).to_be_checked()
    context.close()

    phone = browser.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True)
    page = phone.new_page()
    watch(page, "phone")
    page.goto(BASE)
    log_in(page, sam)
    go_to(page, "Profile")
    page.get_by_role("checkbox", name="Social").tap()
    page.get_by_role("button", name="Save changes").tap()
    expect(page.get_by_role("status").filter(has_text="Profile saved.")).to_be_visible()
    no_horizontal_scroll(page, "phone profile")
    small = small_targets(page, "main.profile-view button")
    assert not small, small
    heights = page.eval_on_selector_all(".profile-choice", "els => els.map(el => el.getBoundingClientRect().height)")
    assert all(h >= 44 for h in heights), heights
    page.screenshot(path=SHOTS / "profile-2-phone.png", full_page=True)
    browser.close()

sql(f"DELETE FROM users WHERE id IN ({alex['id']}, {sam['id']})")
finish()
