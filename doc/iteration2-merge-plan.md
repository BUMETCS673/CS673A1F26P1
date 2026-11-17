# Iteration 2 Merge Plan

## Step 1 – Junshuo: Friends preview (PR #27)

- **Change before merge:** basically none. Optionally add the missing "Overall AI Contribution" and "Notes/Verification" lines to the AI-usage headers of the three files.
- **Merge:** only new files, no conflicts. I already tested the preview in a browser.

## Step 2 – Yuchen: follow backend (PR #29), then the FV-113 docs (PR #24)

- **#29, change before merge:** no code changes. Yuchen runs `tests/live_follows.py` once with the stack running and posts the result on the PR, because I couldn't run it without Docker. Then merge; it doesn't conflict.
- **#24, change before merge:** recreate the commit on current `main`. The edits must go to `code/User_Database/...` instead of the old top-level `User_Database/...` paths, which GitHub marks as conflicting. Also change "Moderate" to a percentage like everyone else. Then merge.

## Step 3 – Ryan + Jibek: event catalog (shared branch, no PR yet)

This is the only step with real work. Ryan's helpers are fine, and Jibek's side does most of what was planned: real pages with a next offset, `GET /api/events/{id}`, Load More with no duplicate events, a details view, and Boston time zone handling. But the branch was built before Ji's login change (FV-120) reached `main`, and it changes some things it shouldn't.

**Changes before merge:**

1. **Rebase onto `main` and fix the conflict in `test_events.py`.** The new tests call `/api/events` without logging in, so after the merge they would all get 401. Use the test login override that `main` already uses (`dependency_overrides[require_user]`).
2. **Don't use test fixtures as the demo data.** `sample_events.json` now contains the test fixtures, so the Nov 17 demo would show titles like "Fixture: yesterday's gallery night". Keep a separate set of realistic sample events in the new start/end format.
3. **Delete `sample_events_backup.json`.** It's an exact copy of the old sample file.
4. **Make the API test independent of today's date.** It expects 5 events plus a next page based on the current time, so it starts failing once the sample events end. Fix the test's reference time, as the assignment asked.
5. **Keep Ji's filter chat working.** The chat's "Filter sample events" mode still expects the old date/time fields, so with the new events it gets a 422 error and shows a misleading message. Do this in the same PR with Ji: either update `filter_demo.py` to the start/end format, or remove that mode, since the recommendation flow replaces it.
6. **Housekeeping:** remove the unused `DemoEvent` import and the duplicate docstring in `test_events.py`, add AI-usage headers to the new or changed files, and use an `[AI] FV-122/FV-123: …` commit message.

- **Merge:** open one PR for the whole branch, and merge once its tests pass on top of `main`.

## Step 4 – Ji: nothing to merge

- FV-124 and FV-120 are already in `main`. Ji's only task is to help with or review the filter-chat fix in Step 3, so `main` is never left with a broken chat.

## Step 5 – Daniel (us)

1. **Merge the Dependabot Vite update (PR #28) first.** It's only a lock file change.
2. **`FV-125-recommendation-results`, changes before merge:**
   - Rebase onto `main` and regenerate `package-lock.json`.
   - Fix the card-title style so the chat's bold-text style doesn't override it.
   - Remove the card's `aria-label` so screen readers also hear the date and location.
   - **Decision needed from you:** upgrade to Vitest 5 to clear the critical test-only security alert, or keep Vitest 3 and dismiss the alert as dev-only. I'd try Vitest 5 first and fall back if it needs a newer Vite.
   - Then open a PR and merge.
3. **`iteration2-infra-prep`: close without merging.** `main` already has the shared login check and guidance on adding protected routes. Its only remaining part, the labeled sections in `api.js`, would now conflict with Jibek's changes to that file.
