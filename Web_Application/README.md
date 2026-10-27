# Boston events website scaffold

This React scaffold demonstrates the planned Boston events layout: a top menu,
an event queue across the left/center, and filters above a chatbot on the right.
It uses plain JavaScript and CSS, with small components teammates can replace
as the real features are implemented. On desktop the right column stretches to
the event queue's height, with long chats scrolling inside their panel. On narrow
screens the panels stack.

To run all three project parts together with Docker, follow
[HOW_TO_START_AND_STOP_PROJECT.md](../HOW_TO_START_AND_STOP_PROJECT.md).
The commands below are an optional frontend-only workflow using local npm.

The Docker workflow also reloads on save: run `./start_project.sh` once from the
repository root, open http://localhost:3000, and keep editing in your normal
editor. Vite sees saved components, CSS, HTML, and sample data without rebuilding
the image. Some changes reload the whole page and may reopen the fake login.
After dependency or Docker/environment configuration changes, rerun the startup
script. The container uses its own dependency volume; host packages are not
used. Startup creates an empty host `node_modules` mount point if needed. Source
files are read-only inside Docker. To check a build there, run
`docker compose --project-directory Web_Application exec website npm run build -- --outDir /tmp/frontend-build`
from the repository root; local `npm run build` still uses local `dist` as usual.

## Run it locally

Install Node.js and npm if they are not already installed. Vite 6 supports
Node.js 18, 20, and 22+. For a new installation, use a supported LTS version
such as Node.js 22 or 24.

From the repository's root folder, run these commands one at a time:

```bash
cd Web_Application
npm install
npm run dev
```

Open the Local URL printed in the terminal (usually `http://localhost:5173`).
Keep the terminal running while using the webpage. Press **Ctrl+C** to stop it.
After editing and saving a source file, Vite automatically updates the page.
Vite is the small development tool that serves the app and builds its files.

No Python server, Docker, API keys, or environment variables are needed for this
scaffold. Its UI uses only local sample data. Messages disappear when you refresh.

## What it does

- Opens a modal labeled **Explicitly fake login** before the website can be used.
- The **Log In (fake for now, click to continue)** button opens the demo without
  checking credentials. This is a visual placeholder, not account security.
- Reload or **Log Out (fake)** returns to the modal; logout clears local demo state.
- Displays six fictional Boston event cards, with expandable sample details.
- Category/date controls filter only those samples, with Clear and an empty state.
  The sample dates are November 1–3, 2026; they are not verified event listings.
- Accepts a chat message with Send or Enter and adds a clearly labeled preset reply.
  Blank messages are ignored; Clear chat resets the conversation.
- Shows disabled Calendar/Friends menu placeholders for future work.

Real registration, login sessions, event data, recommendation behavior, and AI
integration still need to be implemented. The sample filters are local UI
behavior; they do not complete the planned backend filter feature.

## Read the code in this order

1. `index.html`: the HTML page and the empty element where React starts.
2. `src/main.jsx`: attaches the React app to that element and loads the CSS.
3. `src/App.jsx`: the dashboard layout, fake-access flag, and local filter state.
4. `src/components/FakeLogin.jsx`: the native modal and explicit placeholder copy.
5. `src/sampleEvents.js` and `src/components/EventFeed.jsx`: sample data and cards.
6. `src/components/FilterPanel.jsx`: the category/date controls.
7. `src/components/ChatPanel.jsx`: local messages and preset replies.
8. `src/styles.css`: spacing, colors, modal styling, and responsive layout.

JSX is HTML-like syntax inside JavaScript. A component is a function that returns
JSX. `useState` remembers changing information and updates the display when it
changes. Each component keeps its own relevant state; the shared event filters
live in the dashboard so the queue and controls stay synchronized.

`package.json` lists dependencies and commands. React describes the UI,
React DOM displays it in the browser, and Vite provides development/build tools.
`package-lock.json` records the installed dependency versions; keep it in Git.
`node_modules/` contains downloaded packages and `dist/` contains build output;
both are ignored by Git because npm can recreate them.

## Check the build

```bash
npm run build
npm run preview
```

The first command creates a production build in `dist/`. The second serves that
build locally at the URL it prints. Press **Ctrl+C** when finished.

For a quick manual check, confirm the login modal blocks the page until the fake
login button is clicked. Try a category and a sample date, clear the filters,
and try a date with no results. Send a chat message, clear the chat, then log out
and back in. Reload to confirm the fake gate returns. Check a narrow screen too.

## Connect the backend later

The server in `../AI_Movie_Chatbot/app/main.py` currently returns a plain text
status message at `/` and has a FastAPI health endpoint at `/api/health`.
Its API docs are at `http://localhost:8080/docs` in Docker; see
[`../AI_Movie_Chatbot/README.md`](../AI_Movie_Chatbot/README.md).
It does not have a chat API. Once the team adds one, update
`handleSubmit` in `src/components/ChatPanel.jsx` to send the message to it and display the returned
reply and event data. That step will also need loading/error handling.
Keep third-party API keys on the Python server, never in React source files.

## Use the connected development API

Run `bash start_project.sh` from the repository root, then open
http://localhost:3000/api/health/database. Vite forwards `/api` requests to Python,
which runs `SELECT 1` against PostgreSQL. Success is
`{"status":"ok","database":"ok"}`; an unavailable database returns HTTP 503.
`/api/health` checks Python alone. The chat form still uses its labeled sample
replies; feature owners will connect its real endpoints separately.

Use relative API URLs in React so the same code works in Docker and local Vite:

```javascript
const response = await fetch('/api/health/database');
if (!response.ok) throw new Error('The service is temporarily unavailable.');
const result = await response.json();
```

`vite.config.js` forwards `/api` and its subpaths without rewriting them. Docker
sets the server-only `API_PROXY_TARGET=http://api:8000` on the shared network.
For local `npm run dev` with the Docker backend running, it defaults to
`http://127.0.0.1:8080`; open http://localhost:5173/api/health/database to check it.
For a native Python backend on port 8000, copy `.env.example` to `.env.local`
and change the target to `http://127.0.0.1:8000`, then restart Vite.

Only the Vite server reads `API_PROXY_TARGET`. Never put database passwords or API
credentials in frontend environment files or `VITE_` variables. Git and Docker
ignore local environment files. The proxy is a development feature; a production
deployment needs its own `/api` reverse proxy. `npm run preview` is for checking
the static frontend build and is not the connected development workflow.
