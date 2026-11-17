// AI-USAGE SUMMARY
// Authors: Daniel Winnie, Ji Wu, Jibek Kelgenbaeva, Junshuo Huang
// Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; Claude Code (Claude Opus), prompted by Daniel Winnie (auth + API events); OpenAI Codex, prompted by Ji Wu (Chatbox demo integration); ChatGPT (OpenAI), prompted by Jibek Kelgenbaeva (FV-122/FV-123)
// Overall AI Contribution: ~85% (Daniel's parts); 80% (Ji Wu's part); 90% (Jibek's FV-122/FV-123 parts)
// AI-Assisted Areas: app shell, auth state, navigation; the event list, filters, Load More, and chat moved to views/EventsView.jsx
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep; Ji Wu: requirements, prompts, scope decisions, and review of Chatbox demo integration results; Jibek Kelgenbaeva: FV-122/FV-123 requirements, integration, testing, and verification
// Notes/Verification: manual browser testing on localhost:3000 (desktop and narrow widths); FV-122/FV-123 API tests and event catalog verification
// Navigation (Junshuo Huang): OpenAI Codex drafted the navigation code from the team requirements.
// Overall AI Contribution (navigation): 100% of the initial code draft.
// Notes/Verification (navigation): Vite build and navigation smoke test.

import React, { useEffect, useState } from 'react';
import AuthDialog from './components/AuthDialog.jsx';
import EventsView from './views/EventsView.jsx';
import MyPlansView from './views/MyPlansView.jsx';
import FriendsView from './views/FriendsView.jsx';
import ProfileView from './views/ProfileView.jsx';
import { getCurrentUser, logOut } from './api.js';

const pages = ['Events', 'My Plans', 'Friends', 'Profile'];

function Dashboard({ user, onLogout }) {
  const [activePage, setActivePage] = useState('Events');

  return (
    <div className="app-shell">
      <header className="top-bar">
        <button className="brand" type="button" onClick={() => setActivePage('Events')}>
          Boston Events <span>Prototype</span>
        </button>
        <nav aria-label="Main menu">
          {pages.map((page) => (
            <button
              key={page}
              type="button"
              className={activePage === page ? 'nav-current' : undefined}
              aria-current={activePage === page ? 'page' : undefined}
              onClick={() => setActivePage(page)}
            >
              {page}
            </button>
          ))}
        </nav>
        <div className="account-menu">
          {user && <span className="muted-text">Signed in as <strong>{user.display_name || user.username}</strong></span>}
          <button className="secondary-button" type="button" onClick={onLogout}>Log Out</button>
        </div>
      </header>

      {/* Keep the filters and chat state when switching views. */}
      <div hidden={activePage !== 'Events'}>
        <EventsView />
      </div>
      {activePage === 'My Plans' && <MyPlansView />}
      {activePage === 'Friends' && <FriendsView />}
      {activePage === 'Profile' && <ProfileView />}
    </div>
  );
}

export default function App() {
  // null means logged out. The server decides, using the HttpOnly session cookie.
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);

  useEffect(() => {
    // A reload keeps an existing session instead of asking to log in again.
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setCheckingSession(false));
  }, []);

  async function handleLogout() {
    try {
      await logOut();
    } catch {
      // Still lock the page; an unreachable server cannot be asked to forget the session.
    }
    setUser(null);
  }

  if (checkingSession) return null;

  return (
    <>
      <div inert={!user}>
        {/* Changing the key clears filters/messages when the account changes. */}
        <Dashboard key={user ? `user-${user.id}` : 'locked'} user={user} onLogout={handleLogout} />
      </div>
      {!user && <AuthDialog onLogin={setUser} />}
    </>
  );
}
