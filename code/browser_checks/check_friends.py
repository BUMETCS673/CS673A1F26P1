# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)

"""Friends going browser check: three real accounts (Alex, Sam mutual; Pat one-way), each in its own browser."""

from playwright.sync_api import expect, sync_playwright

from common import (BASE, SHOTS, finish, go_to, launch, log_in, no_horizontal_scroll,
                    register_via_api, small_targets, sql, watch)


def open_details(page, title):
    card = page.locator("#events article.event-card", has=page.get_by_role("heading", name=title, exact=True))
    card.get_by_role("button", name="View details").click()
    details = page.locator("#events .panel", has=page.get_by_role("button", name="Close details"))
    expect(details.get_by_role("heading", name=title)).to_be_visible()
    return card, details


def follow(page, account):
    go_to(page, "Friends")
    page.get_by_label("Username").fill(account["username"])
    page.get_by_role("button", name="Search").click()
    page.get_by_role("button", name=f"Follow @{account['username']}").or_(
        page.get_by_role("button", name=f"Follow back @{account['username']}")).first.click()
    expect(page.get_by_role("status").filter(has_text="Now following")).to_be_visible()


with sync_playwright() as p:
    browser = launch(p)
    pages = {}
    probe = browser.new_page()
    accounts = {name: register_via_api(probe, name) for name in ("alex", "sam", "pat")}
    probe.close()
    for name in accounts:
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        watch(page, name)
        page.goto(BASE)
        log_in(page, accounts[name])
        expect(page.locator("#events article.event-card").first).to_be_visible()
        pages[name] = page
    alex, sam, pat = pages["alex"], pages["sam"], pages["pat"]
    title = alex.locator("#events article.event-card h3").nth(1).inner_text()

    # Sam and Pat save the event. Nobody follows anybody yet: Alex sees nobody going.
    for page in (sam, pat):
        card = page.locator("#events article.event-card", has=page.get_by_role("heading", name=title, exact=True))
        card.get_by_role("button", name=f"Save to My Plans: {title}").click()
        expect(card.get_by_text("✓ In My Plans")).to_be_visible()
    _, details = open_details(alex, title)
    alex.wait_for_timeout(500)
    expect(details.locator(".friends-going")).to_have_count(0)

    # Alex follows Sam and Pat; only Sam follows back. Pat stays one-way.
    follow(alex, accounts["sam"])
    follow(alex, accounts["pat"])
    follow(sam, accounts["alex"])
    go_to(alex, "Events")
    _, details = open_details(alex, title)
    expect(details.locator(".friends-going")).to_have_text("Sam is going")
    alex.screenshot(path=SHOTS / "friends-1-details-going.png", full_page=True)

    # Friends page: See plans only for Sam; Sam's plan opens the details view.
    go_to(alex, "Friends")
    expect(alex.get_by_role("button", name="See plans of @" + accounts["sam"]["username"]).first).to_be_visible()
    expect(alex.get_by_role("button", name="See plans of @" + accounts["pat"]["username"])).to_have_count(0)
    alex.get_by_role("button", name="See plans of @" + accounts["sam"]["username"]).first.click()
    panel = alex.get_by_role("region", name="Sam's upcoming plans")
    expect(panel.get_by_text(title)).to_be_visible()
    alex.screenshot(path=SHOTS / "friends-2-friend-plans.png", full_page=True)
    panel.get_by_role("button", name=f"View details: {title}").click()
    expect(alex.locator("#events")).to_be_visible()
    expect(alex.locator("#events .friends-going")).to_have_text("Sam is going")

    # Pat (one-way) cannot read Alex's or Sam's plans, even by calling the API directly.
    for target in ("alex", "sam"):
        assert pat.request.get(f"{BASE}/api/friends/{accounts[target]['id']}/plans").status == 404
    _, pat_details = open_details(pat, title)
    pat.wait_for_timeout(500)
    expect(pat_details.locator(".friends-going")).to_have_count(0)

    # Alex saves too: Sam now sees "Alex is going" after reopening details.
    alex_card, _ = open_details(alex, title)
    alex_card.get_by_role("button", name=f"Save to My Plans: {title}").click()
    expect(alex_card.get_by_text("✓ In My Plans")).to_be_visible()
    go_to(sam, "Events")
    _, sam_details = open_details(sam, title)
    expect(sam_details.locator(".friends-going")).to_have_text("Alex is going")

    # Sam unfollows Alex: access is gone on the next request.
    go_to(sam, "Friends")
    sam.get_by_role("button", name="Unfollow @" + accounts["alex"]["username"]).first.click()
    expect(sam.get_by_role("status").filter(has_text="Unfollowed")).to_be_visible()
    go_to(alex, "Friends")
    alex.reload()
    log_needed = alex.get_by_role("dialog").is_visible()
    assert not log_needed, "reload should keep the session"
    go_to(alex, "Friends")
    expect(alex.get_by_role("heading", name="Followers (0)")).to_be_visible()
    expect(alex.get_by_role("button", name="See plans of @" + accounts["sam"]["username"])).to_have_count(0)
    assert alex.request.get(f"{BASE}/api/friends/{accounts['sam']['id']}/plans").status == 404
    go_to(alex, "Events")
    _, details = open_details(alex, title)
    alex.wait_for_timeout(500)
    expect(details.locator(".friends-going")).to_have_count(0)

    # Phone layout of the Friends page with a friend's plans open.
    phone = browser.new_context(viewport={"width": 360, "height": 740}, is_mobile=True, has_touch=True)
    page = phone.new_page()
    watch(page, "phone")
    page.goto(BASE)
    log_in(page, accounts["sam"])
    follow(page, accounts["alex"])
    go_to(page, "Friends")
    page.get_by_role("button", name="See plans of @" + accounts["alex"]["username"]).first.tap()
    expect(page.get_by_role("region", name="Alex's upcoming plans").get_by_text(title)).to_be_visible()
    no_horizontal_scroll(page, "phone friends")
    small = small_targets(page, "main.friends-view button:not(.text-button)")
    assert not small, f"buttons under 44px on phone: {small}"
    page.screenshot(path=SHOTS / "friends-3-phone.png", full_page=True)
    browser.close()

ids = ", ".join(str(account["id"]) for account in accounts.values())
sql(f"DELETE FROM users WHERE id IN ({ids})")
finish()
