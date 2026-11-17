# Iteration 2 – Remaining Work Assignments

Hey everyone! Here's the plan for the rest of Iteration 2, on top of what we already split up. The goal for the final demo is one complete story with two accounts:

**Sign in → browse Boston events → ask the chat ("music this friday after 6pm near Fenway") → save events to My Plans → follow a friend → see "Alex is going" on an event → sign out and back in, chat history is still there → change preferences in Profile → all of it works on a phone.**

Groups, private messaging, notifications, a real event feed, and an AI model are saved for Iteration 3.

Keep finishing your current task first; the new work comes after. Jira tickets are named below (**NEW** means the ticket will be created soon).

---

## Proposed defaults (say so in Discord by the check-in if you disagree)

- **Friends' plans** are visible only to **mutual follows** (both people follow each other).
- **Chat history:** keep everything, show the last **50** messages on sign-in, with a "Clear history" button.
- **Place matching:** "near Fenway" matches any event whose location contains "Fenway" (ignoring case).
- **Database migrations:** use the next unused number when you merge (003 is Yuchen's follows table).

---

## Junshuo Huang
**Current:** Friends UI (FV-92), then connect it to Yuchen's API.
**New:**
- **App navigation (NEW, small) – do this first, ideally before Nov 17.** Replace the disabled Calendar/Friends menu items with real views: **Events, My Plans, Friends, Profile**. A reload always goes back to Events but stays logged in. Give each view its own file so we don't edit the same lines. Placeholder views are fine at first.
- **Profile and preferences (FV-103, medium).** A Profile view to edit display name and activity preferences, reusing the registration form's checks. Backend: `PATCH /api/auth/me`. Another account must not be able to change yours.

## Yuchen Xu
**Current:** follows storage and API (FV-92, PR #29).
**New:**
- **My Plans (FV-95, medium).** Save and unsave events. A `user_saved_events` table where saving twice doesn't duplicate; `GET /api/plans`, `PUT /api/plans/{event_id}`, `DELETE /api/plans/{event_id}`; a My Plans view grouped by day in Boston time with a "Past" section. Provide a small Save button component that Jibek (details view) and Daniel (chat cards) can drop in. Test with two accounts: one can't see or change the other's plans.

## Ryan (Yung Cheng Chiu)
**Current:** event catalog (FV-122/FV-123) with Jibek, plus the fixes from the merge plan.
**New:**
- **Demo event catalog (NEW, small).** 30–40 realistic fictional Boston events from Nov 17 through the end of the semester: every category, the neighborhoods the parser understands, plus one event crossing midnight, one multi-day event, and one with no location. Keep the test fixtures separate so the demo never shows "Fixture:" titles.
- **Friends going (NEW, small/medium).** "2 friends are going" on the event details view, and a friend's upcoming plans on the Friends page, for **mutual follows only**. Starts once Yuchen's My Plans and follows APIs are in.
- **Preference order (NEW, small).** When a chat request has no category, show the user's preferred categories first. An explicit category always wins.

## Ji Wu
**Current:** connect the parser to the recommendation flow, plus the session checks (FV-120).
**New:**
- **Place matching (NEW, small).** "in/near X" returns only events whose location contains X; an unknown place gets an honest "no matches". Pure function with tests; Daniel calls it from the chat endpoint.
- **Security pass (FV-108, small/medium).** Try XSS payloads in display names, Profile, search, chat, and history, and confirm they show as plain text. Check server-side input limits and that no secrets end up in the frontend build. Write the results into the STD. Prompt-injection testing waits until we add an AI model.
- **Chat speed check (FV-109, small).** Time the chat endpoint with about 10 signed-in sessions at once (p50/p95/max). Confirm sessions don't see each other's results or history. Should be far below 3 seconds; this sets our baseline.

## Daniel Winnie
**Current:** recommendation results UI (FV-125), then connect the parser and catalog to the chat UI and open Jibek's details view from cards.
**New:**
- **Chat history (FV-121, medium).** Save each chat request and reply (what the parser understood plus the event IDs) for the signed-in user; load the last 50 on sign-in; "Clear history". Cards are rebuilt from current catalog data. Test with two accounts: one can't read the other's history.
- **Automatic PR checks (NEW, small).** A GitHub Actions workflow runs the Python tests, frontend tests, and build on every PR, and `main` requires it to pass. This would have caught the broken tests we found in the merge review.
- **Plug the shared pieces into the chat:** Ji's place matching, Ryan's preference order, and Yuchen's Save button on chat cards.

## Jibek Kelgenbaeva
**Current:** event browsing and details (FV-122/FV-123) with Ryan, the two-account demo check, and STD updates.
**New:**
- **Responsive and browser check (FV-110, small/medium).** Test every Iteration 2 screen at phone, tablet, and desktop sizes in Chrome, Firefox, and Safari, plus one real phone. Mark what was emulated. Send bugs to the screen's owner and record the results in the STD.
- **Add Yuchen's Save button and Ryan's "friends going" line to the details view** when they're ready (small).

---

## Everyone
- Update the SDD section for any table or API you add, and give each test result to Jibek for the STD.
- Keep AI-usage headers on every new file, and use `[AI] FV-xxx:` commit messages.
- One feature per branch, with a PR to `main`. Automatic checks must pass once Daniel's workflow is in.

## Order of work
1. **Now:** finish current tasks and merge them (see the merge plan).
2. **Next:** navigation (Junshuo), demo catalog (Ryan), My Plans backend (Yuchen), and place matching (Ji) can all start right away.
3. **Then:** chat history (Daniel), friends going (Ryan), profile (Junshuo), and the checks (Ji, Jibek) build on those.
4. **End of iteration:** two-account demo run, STD/SDD, presentation, and demo video.

If you're blocked, a short note in Discord is enough.
