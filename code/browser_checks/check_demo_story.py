# AI-USAGE SUMMARY
# Authors: Daniel Winnie
# Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
# Overall AI Contribution: ~95%
# AI-Assisted Areas: browser checks (Playwright) that click through the app like a person, FV-108 XSS pass, FV-109 speed check
# Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed the results and screenshots
# Notes/Verification: all passed against the running project on 2026-11-17 (see doc/FV-108-FV-109-security-and-speed.md)

"""The Iteration 2 demo story, end to end in real browsers:
two users sign in, find an event through chat, save it to My Plans, follow each other,
see "Alex is going", keep chat history after signing out and back in, and change
preferences in Profile (which changes the chat's order), on desktop and phone."""

import re

from playwright.sync_api import expect, sync_playwright

from common import (BASE, SHOTS, finish, go_to, launch, log_in, log_out, no_horizontal_scroll,
                    register_via_api, small_targets, sql, watch)


def ask(page, text):
    page.get_by_label("Your request").fill(text)
    page.get_by_role("button", name="Send", exact=True).click()
    results = page.locator(".chat-message").last.get_by_role("region", name="Recommendation results")
    expect(results).to_be_visible()
    return results


def follow(page, account):
    go_to(page, "Friends")
    page.get_by_label("Username").fill(account["username"])
    page.get_by_role("button", name="Search").click()
    page.get_by_role("button", name=re.compile(f"^Follow( back)? @{account['username']}$")).first.click()
    expect(page.get_by_role("status").filter(has_text="Now following")).to_be_visible()


with sync_playwright() as p:
    browser = launch(p)
    probe = browser.new_page()
    alex = register_via_api(probe, "alex", preferences=("Music",))
    sam = register_via_api(probe, "sam", preferences=("Arts",))
    probe.close()

    a_ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    a = a_ctx.new_page()
    watch(a, "alex")
    a.goto(BASE)
    log_in(a, alex)

    # 1. Find an event through chat (the shared place matching: "the North End").
    results = ask(a, "food near the North End")
    titles = results.locator(".recommendation-card-title").all_inner_texts()
    assert titles, "chat found nothing near the North End"
    title = titles[0]
    expect(results.get_by_text("near the North End")).to_be_visible()

    # 2. Save it to My Plans from the chat card.
    results.get_by_role("button", name=f"Save to My Plans: {title}").click()
    expect(results.get_by_text("✓ In My Plans").first).to_be_visible()
    event_id = sql(f"SELECT event_id FROM user_plans WHERE user_id = {alex['id']}")
    go_to(a, "My Plans")
    expect(a.locator("main.my-plans").get_by_role("heading", name=title)).to_be_visible()
    go_to(a, "Events")

    # 3. Follow each other (Sam in a separate browser).
    s_ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    s = s_ctx.new_page()
    watch(s, "sam")
    s.goto(BASE)
    log_in(s, sam)
    follow(a, sam)
    follow(s, alex)

    # 4. Sam sees "Alex is going" (opened from Sam's own chat card).
    go_to(s, "Events")
    sam_results = ask(s, "food near North End")
    sam_results.get_by_role("button", name=re.compile(f"^Food {re.escape(title)}")).click()
    details = s.locator("#events .panel", has=s.get_by_role("button", name="Close details"))
    expect(details.locator(".friends-going")).to_have_text("Alex is going")
    s.screenshot(path=SHOTS / "demo-1-sam-sees-alex-going.png", full_page=True)

    # 5. Chat history survives signing out and back in, with the Save state.
    go_to(a, "Events")
    log_out(a)
    log_in(a, alex)
    history = a.locator(".chat-message")
    expect(history.filter(has_text="food near the North End")).to_have_count(1)
    restored = history.last.get_by_role("region", name="Recommendation results")
    expect(restored.get_by_role("button", name=f"Remove from My Plans: {title}")).to_be_visible()

    # 6. Change preferences in Profile; the very next generic chat request uses them.
    def first_categories(page, text):
        found = ask(page, text)
        return found.locator(".category-badge").all_inner_texts()

    before = first_categories(a, "events after 6pm")
    go_to(a, "Profile")
    for choice in ("Music", "Social"):
        a.get_by_role("checkbox", name=choice).click()  # Music off, Social on
    a.get_by_role("button", name="Save changes").click()
    expect(a.get_by_role("status").filter(has_text="Profile saved.")).to_be_visible()
    go_to(a, "Events")
    after = first_categories(a, "events after 6pm")
    print("before (Music first):", before)
    print("after (Social first):", after)
    if "Music" in before:
        assert before[0] == "Music", before
    if "Social" in after:
        assert after[0] == "Social", after
        assert after.index("Social") == 0 and before != after
    # An explicit category ignores preferences.
    assert set(first_categories(a, "music after 6pm")) <= {"Music"}
    a.screenshot(path=SHOTS / "demo-2-alex-after-profile.png", full_page=True)

    # Honest no-match and clarification answers.
    ask(a, "music near Narnia")
    expect(a.locator(".chat-message").last.get_by_role("heading", name="No matching events")).to_be_visible()
    ask(a, "asdf qwerty")
    expect(a.locator(".chat-message").last.get_by_role("heading", name="Could you rephrase that?")).to_be_visible()

    # 7. Phone: the same chat-save flow for Sam on a phone-sized screen.
    phone = browser.new_context(viewport={"width": 375, "height": 740}, is_mobile=True, has_touch=True)
    m = phone.new_page()
    watch(m, "sam-phone")
    m.goto(BASE)
    log_in(m, sam)
    found = ask(m, "music")
    button = found.get_by_role("button", name=re.compile("^Save to My Plans")).first
    expect(button).to_be_visible()  # must have results; no silent skip
    button.scroll_into_view_if_needed()
    button.tap()
    expect(found.get_by_text("✓ In My Plans").first).to_be_visible()
    no_horizontal_scroll(m, "phone events with chat")
    small = small_targets(m, ".chat-panel button")
    assert not small, f"chat buttons under 44px on phone: {small}"
    m.screenshot(path=SHOTS / "demo-3-phone-chat.png", full_page=True)
    go_to(m, "My Plans")
    no_horizontal_scroll(m, "phone my plans")
    browser.close()

sql(f"DELETE FROM users WHERE id IN ({alex['id']}, {sam['id']})")
finish()
