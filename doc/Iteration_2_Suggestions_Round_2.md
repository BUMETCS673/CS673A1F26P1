# Iteration 2 – Round 2 Status

Hey everyone! The code for Iteration 2 is finished and merged. The full demo works end to end: **two users sign in, find an event through chat, save it to My Plans, follow each other, see "Alex is going" on that event, keep chat history after signing out and back in, and change preferences in Profile, on a phone-sized screen too.**

Every merge passed the automatic PR checks (Python tests, database tests, frontend tests, and build). The whole demo was also clicked through in a real browser with real accounts (`code/browser_checks/`).

| Team member | Merged in Iteration 2 | Still to do |
| --- | --- | --- |
| **Junshuo Huang** | Follow preview (#27); app navigation and the Friends view on the follow API (#40) | STD and presentation (see below) |
| **Yuchen Xu** | Follows storage and API (#29, #24) | STD and presentation; confirm your part of the AI-usage header in `User_Database/init.sql` (it still says "not yet reported") |
| **Ryan (Yung Cheng Chiu)** | Event catalog helpers; demo catalog (#34); preference order (#35), now used by the chat; AI-usage headers (#33) | STD and presentation |
| **Ji Wu** | Parser for time, weekday, and place (#25); login required on events and chat (#26) | STD and presentation |
| **Jibek Kelgenbaeva** | Event browsing and details (#30); responsive layout and browser testing (#41) | One **real-phone** run of the final screens (Save, My Plans, Profile, Friends' plans), added to `doc/FV-110-browser-testing.md`; STD and coordinating the demo run |
| **Daniel Winnie** | Recommendation results, chat integration, chat history, PR checks (#31, #37–#39); finished the remaining Part 2 items: My Plans (#42), friends going (#43), Profile (#44), place matching and chat wiring (#45), security and speed checks | Merge help and demo support |

**For the STD:** the security pass (FV-108) and chat speed check (FV-109) results are in `doc/FV-108-FV-109-security-and-speed.md`, along with the browser checks that cover each demo step. Browser and device results are in `doc/FV-110-browser-testing.md`.

**Defaults that shipped**

- Friends' plans are visible to **mutual follows only**.
- Chat shows the **last 50 messages** on sign-in, with a "Clear history" button.
- "near X" matches an event whose location contains X as whole words, ignoring case, punctuation, and a leading "the"; a landmark such as "Fenway Park" also finds its neighborhood.
- Without a category, the chat lists your preferred categories first.
- Migrations: 003 follows, 004 chat history, 005 My Plans.

**Housekeeping**

- Please move your Jira tickets to Done and check the assignees (FV-95, FV-103, FV-108, FV-109, FV-110, FV-126, FV-127).
- To try the demo yourself: `./start_project.sh`, register two accounts in two browser windows, and follow the story above.

[Jira Backlog](https://f26a1team1.atlassian.net/jira/software/projects/FV/boards/3/backlog)
