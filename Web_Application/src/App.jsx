import React, { useEffect, useState } from 'react';
import AuthDialog from './components/AuthDialog.jsx';
import EventFeed from './components/EventFeed.jsx';
import FilterPanel from './components/FilterPanel.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import { getCurrentUser, getEvents, logOut } from './api.js';

function Dashboard({ user, onLogout }) {
  const [category, setCategory] = useState('');
  const [date, setDate] = useState('');
  // The Python API serves the fictional catalog, sorted by date and time.
  const [catalog, setCatalog] = useState({ status: 'loading', events: [] });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let current = true;
    setCatalog({ status: 'loading', events: [] });
    getEvents()
      .then((events) => current && setCatalog({ status: 'ready', events }))
      .catch(() => current && setCatalog({ status: 'error', events: [] }));
    return () => { current = false; };
  }, [attempt]);

  const visibleEvents = catalog.events.filter((event) => (
    (category === '' || event.category === category)
    && (date === '' || event.date === date)
  ));

  function clearFilters() {
    setCategory('');
    setDate('');
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <a className="brand" href="#events">Boston Events <span>Prototype</span></a>
        <nav aria-label="Main menu">
          <a className="nav-current" href="#events" aria-current="page">Explore events</a>
          <button type="button" disabled>Calendar (later)</button>
          <button type="button" disabled>Friends (later)</button>
        </nav>
        <div className="account-menu">
          {user && <span className="muted-text">Signed in as <strong>{user.display_name || user.username}</strong></span>}
          <button className="secondary-button" type="button" onClick={onLogout}>Log Out</button>
        </div>
      </header>

      <main id="events" className="dashboard">
        <div className="page-heading">
          <p className="eyebrow">Discover Boston</p>
          <h1>Find your next plan.</h1>
          <p>Browse events, narrow your choices, and plan with a chat.</p>
          <p className="prototype-note">
            Demo: accounts are stored in the project database; the fictional events come from the Python API.
            Choose a chat action to try request parsing or sample event filtering.
          </p>
        </div>

        <div className="dashboard-grid">
          <EventFeed
            status={catalog.status}
            events={visibleEvents}
            onClearFilters={clearFilters}
            onRetry={() => setAttempt((count) => count + 1)}
          />
          <aside className="dashboard-sidebar" aria-label="Filters and event chat">
            <FilterPanel
              events={catalog.events}
              category={category}
              date={date}
              onCategoryChange={setCategory}
              onDateChange={setDate}
              onClear={clearFilters}
            />
            <ChatPanel events={catalog.events} />
          </aside>
        </div>
      </main>
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
