# Iteration 2 – Jira Drafts (not yet inserted)

Project: **FV** · Epic: **FV-97** · Sprint: **FV Sprint 2: Iteration 2**

This file lists every Jira change needed for the Iteration 2 assignment, in the same
format as the existing FV stories. Nothing here has been sent to Jira yet.

- **Part 1** updates tickets that already exist (assignee, sprint, scope).
- **Part 2** creates new tickets.
- **Part 3** is housekeeping on existing tickets.

Every new or updated ticket ends with the standard definition of done used on FV-92 to FV-110:

> Connect the React UI, Python API, and PostgreSQL persistence where applicable. Verify the
> listed acceptance scenarios with representative accounts and fixtures, including
> unauthorized-access and failure cases. Update relevant setup/API documentation. A static
> demo or placeholder response does not meet these criteria.

## Proposed defaults (confirm in Discord before insertion)

1. **Friends' plans visibility:** only **mutual follows** (A follows B and B follows A) can see each other's saved events.
2. **Chat history:** keep everything; load the most recent **50** messages on sign-in; the user can clear their own history.
3. **Place matching:** "in/near X" matches an event when its location contains X, ignoring case ("near Fenway" matches "Fenway, Boston").
4. **Migrations:** 003 = follows (Yuchen). New tables take the next unused number in merge order (expected 004 = chat history, 005 = saved events).

---

## Part 1 – Existing tickets to update

### FV-121 – Save and restore chat history per signed-in user
- **Type:** Subtask (parent FV-72) · **Assignee:** Daniel Winnie · **Sprint:** FV Sprint 2 (already) · **Status:** To Do
- **Change:** replace the description (the current one says migration 003, which follows now uses).

**Description**

## User story
As a signed-in user, I want my chat requests and the assistant's answers saved so that I can see them again after signing out and back in.

## Acceptance criteria
1. Each chat request and its structured reply (parser interpretation and matched event IDs) is stored for the signed-in user only.
2. On sign-in, the chat shows that user's most recent 50 exchanges in order. Event cards are rebuilt from current catalog data, so ended or missing events are labeled unavailable instead of shown with stale details.
3. "Clear history" removes only the signed-in user's messages; after a reload the chat is empty.
4. User A cannot list, read, or delete user B's history by changing an ID or request body (tested with two accounts).
5. A failed save shows a clear error and is not displayed as saved.

## Implementation context
Add a `chat_messages` migration (next unused number, expected `004_chat_messages.sql`) with `user_id` FK (ON DELETE CASCADE), `request_text`, `reply` (JSONB), `created_at`. Expose `GET /api/chat/history` and `DELETE /api/chat/history` on the protected router; the chat endpoint writes each exchange. Store event IDs, not rendered text.

## Dependencies
- Chat endpoint built in the FV-99/FV-125 integration (Daniel)
- FV-72 sessions (done)

### FV-95 – Add or remove personal calendar entries without changing group events
- **Type:** Story (parent FV-97) · **Assignee:** Yuchen Xu · **Sprint:** FV Sprint 2 (already)
- **Change:** set the assignee and append the "Iteration 2 scope" section below. Keep the original description: the group-related criteria (2–4) remain for Iteration 3.

**Append to description**

## Iteration 2 scope ("My Plans")
Groups (FV-93/94) are not in Iteration 2, so this iteration delivers only the personal part.

Acceptance for Iteration 2:
1. A signed-in user can save an upcoming event from the event list, the details view, or a chat card. Saving again does not create a duplicate (204 both times).
2. A "My Plans" view lists the user's saved events grouped by day in Boston local time, soonest first, with ended events in a separate "Past" section.
3. Removing a saved event affects only this user's plans; the event stays in the catalog and in other users' plans.
4. Another account cannot read or change these plans by changing an ID (two-account test).
5. Saved state survives reload and sign-in; the Save button shows "Saved" for events already saved.

Implementation: `user_saved_events (user_id, event_id, saved_at)` with a primary key on `(user_id, event_id)` (next unused migration number). Endpoints `GET /api/plans`, `PUT /api/plans/{event_id}` (404 for an unknown event), `DELETE /api/plans/{event_id}`. Reuse the follows endpoints' patterns. Coordinate the Save button placement with Jibek (details view) and Daniel (chat cards).

Dependencies: FV-98 catalog with stable IDs (FV-122/123 branch).

### FV-103 – Change activity preferences from the user profile
- **Type:** Story (parent FV-97) · **Assignee:** Junshuo Huang · **Sprint:** add FV Sprint 2
- **Change:** set the assignee and sprint, and append the scope note below. Keep the original description.

**Append to description**

## Iteration 2 scope
A Profile view (in the new navigation, FV-NEW-6) shows display name, email (read-only), and activity preferences. Saving uses a new `PATCH /api/auth/me` that accepts `display_name` and `activity_preferences` with the same validation as registration. Empty preferences: **allowed** (proposed; confirm). Using saved preferences for default ordering is subtask FV-NEW-4 (Ryan).

### FV-108 – Protect API secrets and defend user inputs against XSS and prompt injection
- **Type:** Task (parent FV-97) · **Assignee:** Ji Wu · **Sprint:** add FV Sprint 2
- **Change:** append the scope note below.

**Append to description**

## Iteration 2 scope
No AI model is used in Iteration 2, so criteria 5 and 6 (prompt injection) are deferred to the iteration that adds one. Iteration 2 covers criteria 1–4 and 7 on implemented surfaces: registration and profile fields, user search, chat requests and stored history, and saved plans. Representative stored and reflected XSS payloads must render as plain text. Record the results in the STD.

### FV-109 – Meet the three-second chatbot response target under concurrent sessions
- **Type:** Task (parent FV-97) · **Assignee:** Ji Wu · **Sprint:** add FV Sprint 2
- **Change:** append the scope note below.

**Append to description**

## Iteration 2 scope
Measure the rule-based chat endpoint (no external model yet). Proposed test conditions, to confirm: Docker on a team laptop, 10 concurrent signed-in sessions, 5 requests each, demo catalog (FV-NEW-1). Report p50/p95/max time to rendered cards and every breach, and check that each session's results and history stay separate. Label these as stub-free but model-free numbers; re-measure when a model is added.

### FV-110 – Make the web UI responsive and verify desktop/mobile browser compatibility
- **Type:** Task (parent FV-97) · **Assignee:** Jibek Kelgenbaeva · **Sprint:** add FV Sprint 2
- **Change:** append the scope note below.

**Append to description**

## Iteration 2 scope
Verify the screens delivered in Iteration 2: sign-in/registration, events list and details, chat with result cards, My Plans, Friends, and Profile. Use phone (360–390 px), tablet (768 px), and desktop (1280 px+) viewports in Chrome, Firefox, and Safari/WebKit, plus at least one real phone. Mark emulated results as emulated. Bugs found go to the owner of each screen.

### FV-92 – Find users by username and add or remove friends
- **No change to the description.** Already assigned (Junshuo UI, Yuchen API) and in Sprint 2. Listed here only so the full Iteration 2 set is in one place.

---

## Part 2 – New tickets to create

### FV-NEW-1 – Realistic demo event catalog, separate from test fixtures
- **Type:** Subtask · **Parent:** FV-98 · **Assignee:** Yung Cheng Chiu (Ryan) · **Sprint:** FV Sprint 2 · **Estimate:** S

## User story
As a demo viewer, I want the app to show realistic Boston events over the coming weeks so that browsing, chat, and plans look like the real product.

## Acceptance criteria
1. `app/data/sample_events.json` holds 30–40 fictional events in the catalog format (`id, title, category, start, end, location, description`) from 2026-11-17 through the end of the semester, with no "Fixture" wording.
2. Every category (Music, Arts, Food, Outdoors, Social) has at least five events, and every neighborhood the parser recognizes in team examples (e.g. Fenway, Back Bay, North End, Allston, Seaport, Cambridge) appears at least once.
3. Includes at least one event that crosses midnight, one multi-day event, and one with an empty location (shown as "Location unavailable").
4. Test fixtures stay in `tests/fixtures/` and the API tests keep using a fixed reference time, so tests don't depend on this file or on today's date.
5. Every event is clearly fictional; no real venue bookings or ticket links.

## Dependencies
FV-122/FV-123 catalog branch merged.

### FV-NEW-2 – Match chat place requests against event locations
- **Type:** Subtask · **Parent:** FV-99 · **Assignee:** Ji Wu · **Sprint:** FV Sprint 2 · **Estimate:** S

## User story
As a user, I want "near Fenway" or "in Back Bay" to return events in that area so that location requests work.

## Acceptance criteria
1. A request with a location returns only events whose location contains the requested place, ignoring case and extra spaces ("near fenway" matches "Fenway, Boston").
2. A place that matches no event in the catalog gives the honest "no matches" reply; it is not silently dropped.
3. Combined with category, date, and time, all constraints apply together (FV-99 AC2).
4. Unit tests use the demo catalog or fixtures with a fixed Boston reference time.

## Implementation context
Add a pure function next to the catalog helpers, and call it from the chat endpoint (Daniel). Agree the rule in Discord first (proposed default 3 above).

### FV-NEW-3 – See which friends are going to an event
- **Type:** Story · **Parent:** FV-97 · **Assignee:** Yung Cheng Chiu (Ryan) · **Sprint:** FV Sprint 2 · **Estimate:** S/M

## User story
As a signed-in user, I want to see which of my friends have saved an event so that we can plan to go together.

## Acceptance criteria
1. The event details view shows "N friends are going" with their display names, counting only **mutual follows** who saved the event. It shows nothing when there are none.
2. On the Friends page, selecting a mutual follow shows that friend's upcoming saved events (titles, Boston time, location); each one opens the details view.
3. A non-mutual follower, or a stranger who changes an ID, gets 403/404 and no plan data (two- and three-account tests).
4. Unfollowing immediately removes access; a reload shows no friend plans.

## Implementation context
Endpoints `GET /api/events/{event_id}/friends-going` and `GET /api/friends/{user_id}/plans`, joining `user_follows` (both directions) with `user_saved_events`. UI: one line in Jibek's details view and a section in Junshuo's Friends page; coordinate placement with them.

## Dependencies
FV-95 My Plans (Yuchen), FV-92 follows API (Yuchen).

### FV-NEW-4 – Order the default event list by saved activity preferences
- **Type:** Subtask · **Parent:** FV-103 · **Assignee:** Yung Cheng Chiu (Ryan) · **Sprint:** FV Sprint 2 · **Estimate:** S

## Acceptance criteria
1. When a chat request has no category ("something fun this weekend"), matching events in the user's preferred categories come first, then the rest, each group in start-time order.
2. An explicit category in the request always overrides preferences.
3. Users with no preferences get plain start-time order.
4. After a preference change (FV-103), the next request uses the new preferences without signing in again.
5. Unit tests cover all four cases with fixtures.

## Implementation context
A pure helper next to `sort_by_start`; the chat endpoint (Daniel) passes the current user's preferences into it.

### FV-NEW-5 – Run tests and build automatically on every pull request
- **Type:** Task · **Parent:** FV-97 · **Assignee:** Daniel Winnie · **Sprint:** FV Sprint 2 · **Estimate:** S

## Purpose
Catch broken tests before merge. During the Iteration 2 merge review, a branch's tests would have returned 401 after merging, and another test would have broken on a future date.

## Acceptance criteria
1. A GitHub Actions workflow runs on every PR to `main` and every push to `main`: Python unit tests (`tests/test_*.py`), frontend tests (`npm test`), and the production build (`npm run build`).
2. Database-only `live_*.py` tests run against a PostgreSQL service container with all migrations applied (or are documented as manual if that isn't feasible).
3. `main` branch protection requires the workflow to pass before merging (needs a repo admin).
4. The README explains how to read a failed run and rerun it.
5. The workflow uses no secrets; forks' PRs run safely.

### FV-NEW-6 – Replace placeholder menu items with real app navigation
- **Type:** Task · **Parent:** FV-97 · **Assignee:** Junshuo Huang · **Sprint:** FV Sprint 2 · **Estimate:** S

## Purpose
Give every Iteration 2 feature a place in the app instead of separate preview pages.

## Acceptance criteria
1. The top menu has **Events** (homepage: event list, filters, chat), **My Plans**, **Friends**, and **Profile**; the current view is highlighted, and the disabled placeholders are gone.
2. Every full page load, including reload, starts on Events while keeping a valid session (FV-72 AC6/AC7); no router library is required.
3. Each view has its own component file, so owners work in separate files: `MyPlansView.jsx` (Yuchen), `FriendsView.jsx` (Junshuo), `ProfileView.jsx` (Junshuo).
4. Works with keyboard and at phone width (menu wraps or collapses without page-wide horizontal scroll).
5. Lands early (target: before the Nov 17 check-in) so the others can plug in; placeholder views are fine at first.

---

## Part 3 – Housekeeping (on insertion)

- **FV-72, FV-98, FV-99** are marked **Done**, but their acceptance criteria are only partly met (chat history, catalog details, chat flow). **Proposed:** move them back to In Progress until their Iteration 2 subtasks are done.
- **FV-122, FV-123:** assign Yung Cheng Chiu (backend) and Jibek Kelgenbaeva (UI); status In Progress.
- **FV-125:** assign Daniel Winnie; status In Progress.
- **FV-120:** move to Done once PR #26 (merged) is confirmed. It is still In Progress.

## Insertion checklist (for later)

1. Look up the Jira account IDs for all six members.
2. Create FV-NEW-1 to FV-NEW-6 with the parents above, then replace the `FV-NEW-n` cross-references with the real keys.
3. Apply the Part 1 updates and the Part 3 status changes.
4. Add every ticket to "FV Sprint 2: Iteration 2".
