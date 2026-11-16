# Iteration 2 – Suggestions for Round 2

Hey everyone! Here's where things stand and what I'd suggest each of us does to finish Iteration 2. The goal hasn't changed: **two users sign in, find an event through chat, save it to My Plans, follow each other, see "Alex is going" on that event, keep chat history after signing out and back in, and change preferences in Profile, all on a phone-sized screen too.**

**Merged on Nov 15:** Ryan's demo catalog (#34), preference order (#35), and AI-usage headers (#33), plus the Dependabot update (#32). **Open for review from Daniel:** automatic PR checks (#39), the real chat endpoint (#37: `POST /api/chat`, with cards that open the details view), and chat history (#38, migration **004**). Once #39 merges, every PR runs the Python tests, the database tests, the frontend tests, and the build automatically.

| Team member | Where things stand | Next (independent coding) | Then (integration) |
| --- | --- | --- | --- |
| **Junshuo Huang** | The follow preview is merged (#27), but it still uses mock accounts, and the menu still shows "Friends (later)". Nothing pushed for navigation yet. | **App navigation first, as soon as possible.** Everyone else's screens need somewhere to go: Events, My Plans, Friends, and Profile, each in its own file. Placeholder views are fine. Then **connect the Friends view to Yuchen's API** (`/api/users/search`, `/api/following`, `/api/followers`) and check that a follow survives a reload. | **Profile and preferences (FV-103)** through `PATCH /api/auth/me`, reusing the registration checks. Verify with two accounts that one can't change the other's profile. |
| **Yuchen Xu** | The follows API is merged (#29, #24). My Plans hasn't started, and Ryan, Jibek, and Daniel all depend on it. | **My Plans storage and API (FV-95), as soon as possible.** Use migration **005** (004 is chat history). Add `GET /api/plans`, `PUT /api/plans/{event_id}` (404 for an unknown event), and `DELETE /api/plans/{event_id}`. Add a `live_plans.py` with two accounts, modeled on `live_follows.py`; the PR checks (#39) run it automatically. | The My Plans view (grouped by day in Boston time, with a "Past" section) and **a small Save button component**. Post its props in Discord so Jibek and Daniel can add it to the details view and chat cards. **Also:** confirm your part of the AI-usage header in `User_Database/init.sql`, which still says "not yet reported". |
| **Ryan (Yung Cheng Chiu)** | Catalog, demo catalog, and preference order are all merged. Nice work! | **Small follow-up to the demo catalog (FV-126).** The ticket also asks for one event that crosses midnight, one multi-day event, and one with an empty location (shown as "Location unavailable"). Cambridge is also missing. Add them to `sample_events.json` and extend the `DemoDataTests` check. | **Friends going (new ticket)** once Yuchen's plans API is in: "2 friends are going" on event details and a friend's upcoming plans on the Friends page, mutual follows only. Coordinate placement with Jibek (details view) and Junshuo (Friends view). Daniel will plug your preference-order helper into the chat. |
| **Ji Wu** | FV-120 and FV-124 are merged. Place matching, FV-108, and FV-109 haven't started. | **Place matching (new ticket), now a smaller job.** Daniel's chat PR (#37) has a temporary `matches_place()` in `app/chat.py` using our agreed rule ("near X" matches a location containing X, ignoring case). Move it into a shared helper next to the catalog helpers, add your fixed-time tests, and handle any cases it misses. The chat already gives an honest "no matches" for an unknown place. | **Security pass (FV-108) and chat speed check (FV-109)** once Daniel's chat and history PRs (#37, #38) are merged. Test XSS in display names, search, chat requests, and saved history; check that no secrets are in the frontend build; and time `POST /api/chat` with about 10 sessions at once. Send the results to Jibek for the STD. |
| **Jibek Kelgenbaeva** | Event browsing and details are merged (#30). The device and browser check (FV-110) hasn't started. | **Device and browser test plan (FV-110).** Phone (360–390 px), tablet (768 px), and desktop (1280 px+) in Chrome, Firefox, and Safari, plus one real phone, and mark what was emulated. Start now on the current screens and rerun at the end. **Heads-up:** Daniel's chat PR (#37) makes a small change to `EventFeed.jsx` so a chat card can open your details view; please review that part of #37. **Also:** confirm your tools and AI percentage in the headers of `app/routes/events.py` and `tests/test_events.py`, which still say "to be confirmed by the author". | Add Yuchen's Save button and Ryan's "friends going" line to the details view when they're ready. Then run the full check on the finished screens, record it in the STD, and coordinate the final two-account demo run. |

**Critical path:** Junshuo's navigation and Yuchen's My Plans API unblock almost everything else, so please prioritize those two. If either is stuck, post in Discord early and someone can pair with you.

**Defaults** (unchanged from Part 2)

- Friends' plans are visible to **mutual follows only**.
- Chat shows the **last 50 messages** on sign-in, with a "Clear history" button.
- "near X" matches any event whose location **contains X**, ignoring case.
- Database migrations use the **next unused number** when you merge: 003 is follows, 004 is chat history, and 005 should be My Plans.

**Working on it**

- Start each branch from the latest `main`, keep one feature per branch, and open a PR to `main`. Once the PR checks (#39) are in, a red X means a test or the build failed. Click **Details** to see which step failed.
- New migrations must be safe to run twice (`IF NOT EXISTS`), because the checks apply `init.sql` and then every migration.
- Update the SDD for any table or API you add, give your test results to Jibek for the STD, and use `[AI] FV-xxx:` commit messages with AI-usage headers on new files.
- Please check that your Jira tickets are assigned to you and moved out of Icebox (FV-95, FV-103, FV-108, FV-109, FV-110).
- If you're blocked, drop a short note in Discord. A quick note is enough.

[Jira Backlog](https://f26a1team1.atlassian.net/jira/software/projects/FV/boards/3/backlog)
