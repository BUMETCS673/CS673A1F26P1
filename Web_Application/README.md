# Basic movie chatbot webpage

This is a small React frontend based on the core chat and movie discovery ideas
in `../iteration0/README.md` and the SPPP. It lives beside `../AI_Movie_Chatbot`.
It uses plain JavaScript and CSS, with comments explaining each part.

To run all three project parts together with Docker, follow
[HOW_TO_START_AND_STOP_PROJECT.md](../HOW_TO_START_AND_STOP_PROJECT.md).
The commands below are an optional frontend-only workflow using local npm.

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
demo. Nothing is sent to the backend. Messages disappear when you refresh.

## What it does

- Displays an introduction and a chat form.
- Accepts a message using Send or Enter; ignores blank messages.
- Adds your message and a clearly labeled sample bot reply to the conversation.
- Shows the same three sample movies after any message.
- Clears the conversation and sample recommendations with Clear chat.

The demo does **not** understand requests or recognize preferences yet.
AI recommendations, real movie data, posters, ratings, watchlists, and other
features from the proposal are future work.

## Read the code in this order

1. `index.html`: the HTML page and the empty element where React starts.
2. `src/main.jsx`: attaches the React app to that element and loads the CSS.
3. `src/App.jsx`: the page, example movie data, and chat behavior in one component.
4. `src/styles.css`: basic spacing, colors, and layout.

JSX is HTML-like syntax inside JavaScript. A component is a function that returns
JSX. `useState` remembers changing information and updates the display when it
changes. This app only needs two pieces of state: the input and the messages.

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

For a quick manual check, send a message with Enter, send another with the button,
check that both appear and the samples display, and then clear the chat. Check
that blank messages cannot be sent and the page fits a narrow browser window.

## Connect the backend later

The server in `../AI_Movie_Chatbot/app/main.py` currently returns a plain text
status message at `/` and has a FastAPI health endpoint at `/api/health`.
Its API docs are at `http://localhost:8080/docs` in Docker; see
[`../AI_Movie_Chatbot/README.md`](../AI_Movie_Chatbot/README.md).
It does not have a chat API. Once the team adds one, update
`handleSubmit` in `src/App.jsx` to send the message to it and display the returned
reply and movie data. That step will also need loading/error handling.
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
