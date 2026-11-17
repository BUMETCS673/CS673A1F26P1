# Iteration 2 Team Assignments – Part 2

Hey everyone! Here's the proposed split for the rest of Iteration 2, on top of what we're already doing. Finish your current task first, then move to the new ones. Our **final Iteration 2 demo** goal is to show two users signing in, finding an event through chat, saving it to **My Plans**, following each other, seeing **"Alex is going"** on that event, keeping chat history after signing out and back in, and changing preferences in **Profile**, all on a phone-sized screen too.

| Team member | Current work (finish first) | Next (independent coding) | Then (integration) |
| --- | --- | --- | --- |
| **Junshuo Huang** | Friends UI (FV-92), connected to Yuchen's API | **App navigation (new ticket).** Replace the disabled menu placeholders with Events, My Plans, Friends, and Profile views, each in its own file. A reload returns to Events but keeps you logged in. Placeholder views are fine; ideally done before Nov 17 so everyone can plug in. | **Profile and preferences (FV-103).** Edit display name and activity preferences through `PATCH /api/auth/me`, reusing the registration checks. Verify that another account can't change yours. |
| **Yuchen Xu** | Follow storage and API (FV-92, PR #29) | **My Plans storage (FV-95).** Draft the migration and storage functions to save, list, and remove events. Use two local test accounts to check persistence and that saving twice doesn't duplicate. | Expose the plans through authenticated APIs, build the My Plans view (grouped by day in Boston time, with a "Past" section), and share a Save button that Jibek and Daniel can reuse. |
| **Ryan (Yung Cheng Chiu)** | Event catalog (FV-122, FV-123) with Jibek, plus the merge fixes | **Demo catalog (new ticket).** Write 30–40 realistic fictional Boston events through the end of the semester, covering every category and neighborhood, kept separate from the test fixtures. **Preference order (new ticket).** A helper that puts preferred categories first when a chat request has no category, tested with fixtures. | **Friends going (new ticket).** Once Yuchen's plans API is in, show "2 friends are going" on event details and a friend's upcoming plans on the Friends page, for mutual follows only. |
| **Ji Wu** | Connect the parser to the recommendation flow and protect routes (FV-120) | **Place matching (new ticket).** A function that keeps only events whose location contains the requested place ("near Fenway"), with tests that use a fixed Boston date and time. An unknown place gives an honest "no matches". | **Security pass (FV-108) and chat speed check (FV-109)** on the connected app: XSS checks on every text input, no secrets in the frontend build, and response times with about 10 sessions at once. Send the results to Jibek for the STD. |
| **Daniel Winnie (me)** | Recommendation results UI (FV-125), then connect the parser and catalog to the chat | **Automatic PR checks (new ticket).** A GitHub Actions workflow that runs the Python tests, frontend tests, and build on every PR. **Chat history storage (FV-121).** Draft the migration and storage, checked with two local test accounts. | Load the last 50 messages on sign-in and add "Clear history". Plug Ji's place matching, Ryan's preference order, and Yuchen's Save button into the chat. |
| **Jibek Kelgenbaeva** | Event browsing and details (FV-122, FV-123) with Ryan, plus the demo check and STD | **Device and browser test plan (FV-110).** Set up the phone, tablet, and desktop sizes and the Chrome, Firefox, and Safari matrix, and try it on the current screens. | Add the Save button and "friends going" line to the details view. Run the full check on the finished screens, record it in the STD, and coordinate the final two-account demo run. |

**Proposed defaults** (say so in Discord if you disagree)

- Friends' plans are visible to **mutual follows only**.
- Chat shows the **last 50 messages** on sign-in, with a "Clear history" button.
- "near X" matches any event whose location **contains X**, ignoring case.
- Database migrations use the **next unused number** when you merge (003 is Yuchen's follows).

**Working on it**

- Keep one feature per branch, with a PR to `main`. Use local fixtures or two local test accounts until the piece you depend on is merged.
- Update the SDD for any table or API you add, and give your test results to Jibek for the STD.
- If you're blocked, drop a short note in Discord. A quick note is enough.

**Quick check-in**

- We'll go over what merged, any blockers that need the whole group, and the plan for the final demo and presentation.
- The people working on each feature can sort out API details in Discord and post the decision there.

[Jira Backlog](https://f26a1team1.atlassian.net/jira/software/projects/FV/boards/3/backlog)
