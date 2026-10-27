import React, { useState } from 'react';
import FakeLogin from './components/FakeLogin.jsx';
import EventFeed from './components/EventFeed.jsx';
import FilterPanel from './components/FilterPanel.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import { sampleEvents } from './sampleEvents.js';

function Dashboard({ onLogout }) {
  const [category, setCategory] = useState('');
  const [date, setDate] = useState('');

  // These filters work only on our fictional local samples. Replace the source
  // with the event API later; the feed and chatbot should share one catalog.
  const visibleEvents = sampleEvents.filter((event) => (
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
        <button className="secondary-button" type="button" onClick={onLogout}>Log Out (fake)</button>
      </header>

      <main id="events" className="dashboard">
        <div className="page-heading">
          <p className="eyebrow">Discover Boston</p>
          <h1>Find your next plan.</h1>
          <p>Browse events, narrow your choices, and plan with a chat.</p>
          <p className="prototype-note">
            Demo: fictional events with request parsing and sample event filtering in chat.
            Choose a chat action to try each feature. Real accounts and an authoritative event catalog are future work.
          </p>
        </div>

        <div className="dashboard-grid">
          <EventFeed events={visibleEvents} onClearFilters={clearFilters} />
          <aside className="dashboard-sidebar" aria-label="Filters and event chat">
            <FilterPanel
              category={category}
              date={date}
              onCategoryChange={setCategory}
              onDateChange={setDate}
              onClear={clearFilters}
            />
            <ChatPanel events={sampleEvents} />
          </aside>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  // This flag is a visual demo gate, not authentication. Reloading locks it again.
  // Replace it with real server-verified sessions when login is implemented.
  const [hasDemoAccess, setHasDemoAccess] = useState(false);

  return (
    <>
      <div inert={!hasDemoAccess}>
        {/* Changing the key clears local filters/messages when leaving the demo. */}
        <Dashboard key={hasDemoAccess ? 'demo' : 'locked'} onLogout={() => setHasDemoAccess(false)} />
      </div>
      {!hasDemoAccess && <FakeLogin onContinue={() => setHasDemoAccess(true)} />}
    </>
  );
}
