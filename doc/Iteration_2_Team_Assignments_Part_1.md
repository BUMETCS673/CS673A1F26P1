# Iteration 2 Team Assignments

Hey everyone! Here’s the proposed split for Iteration 2. Let’s do a **10–15 minute check-in on Tuesday, Nov 10, or Wednesday, Nov 11**. Our **Nov 17 demo** goal is to show a user signing in, browsing Boston events, finding an event through chat, and adding a friend.

| Team member | Iteration 1 work | Before the meeting (independent coding) | After the meeting (integration) |
| --- | --- | --- | --- |
| **Junshuo Huang (me)** | Registration and login forms (FV-114, FV-115) | **Friends UI (FV-92).** Build a standalone React preview for username search, the friends list, and add/remove actions. Use two mock accounts and local state to show the flow. | Connect the UI to Yuchen’s API and verify that changes survive a reload. |
| **Yuchen Xu** | Account fields and database migration (FV-113) | **Friendship storage (FV-92).** Draft the PostgreSQL migration and storage functions for add, list, and remove. Use two local test accounts to check persistence and duplicate adds. | Confirm how adding a friend should work, then expose the agreed operations through authenticated APIs. |
| **Ryan (Yung Cheng Chiu)** | Sample Boston events and event API (FV-116) | **Event catalog (FV-122, FV-123).** Use local event fixtures to implement and test the backend logic for filtering ended events, sorting by start time, and returning pages without duplicate IDs. Use a fixed reference time in tests. | Agree on the event fields and pagination response with Jibek, then wire the logic into the events API. |
| **Ji Wu** | Event filtering and chat request parsing (FV-117, FV-118) | **Chat parser (FV-124).** Extend the existing parser for time, weekday, and location. Check a few example phrases with a fixed Boston date and time in the parser tests. | Connect the parser to Daniel’s recommendation flow and apply the shared session check to protected routes (FV-120). |
| **Daniel Winnie** | FastAPI setup, stack integration, and registration/login/session integration (FV-111, FV-112, FV-119) | **Recommendation results UI (FV-125).** Build a standalone React component for event cards, clarification, and no matches. Use local mock responses and a placeholder card-click callback. | Connect the parser and event catalog to the chat UI. Use the shared event ID to open Jibek’s details view. |
| **Jibek Kelgenbaeva** | QA planning and project documentation | **Event browsing UI (FV-122, FV-123).** Build a standalone React preview for event details in Boston local time. Use local mock data to demonstrate Load More, an empty list, and a loading error. | Connect the preview to Ryan’s API, wire up event details, and coordinate the two-account demo check and STD updates. |

**Before we meet**

- Work on your own branch using local fixtures, mock responses, or a local test database. Keep new UI components in standalone previews until we start integrating.
- If you’re blocked, drop a short note in Discord. A quick note is enough.

**Quick check-in**

- I’ll briefly summarize where we are. We’ll discuss any blockers that need the whole group and confirm the next step for the Nov 17 demo.
- The people working on each feature can sort out API details in Discord and post the decision there.

[Jira Backlog](https://f26a1team1.atlassian.net/jira/software/projects/FV/boards/3/backlog)
