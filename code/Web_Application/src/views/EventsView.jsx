// AI-USAGE SUMMARY
// Authors: Daniel Winnie, Ji Wu
// Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; Claude Code (Claude Opus), prompted by Daniel Winnie (auth + API events); OpenAI Codex, prompted by Ji Wu (Chatbox demo integration)
// Overall AI Contribution: ~85% (Daniel's parts); 80% (Ji Wu's part)
// AI-Assisted Areas: dashboard layout, auth state, event loading and filtering; Chatbox demo integration (Ji Wu); chat cards open event details (FV-125)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep; Ji Wu: requirements, prompts, scope decisions, and review of Chatbox demo integration results
// Notes/Verification: manual browser testing on localhost:3000 (desktop and narrow widths)
// Navigation extraction (Junshuo Huang): OpenAI Codex drafted the move.

import React, { useEffect, useState } from 'react';
import EventFeed from '../components/EventFeed.jsx';
import FilterPanel from '../components/FilterPanel.jsx';
import ChatPanel from '../components/ChatPanel.jsx';
import { getEvents } from '../api.js';

export default function EventsView() {
  const [category, setCategory] = useState('');
  const [date, setDate] = useState('');
  // The Python API serves the fictional catalog, sorted by date and time.
  const [catalog, setCatalog] = useState({
    status: 'loading',
    events: [],
    nextOffset: null,
  });
  const [attempt, setAttempt] = useState(0);
  // A chat card asks the event feed to open its details view. A new object each
  // time, so clicking the same card twice opens it again.
  const [detailsRequest, setDetailsRequest] = useState(null);

  useEffect(() => {
    let current = true;

    setCatalog({
      status: 'loading',
      events: [],
      nextOffset: null,
    });

    getEvents(5, 0)
      .then((data) => {
        if (current) {
          setCatalog({
            status: 'ready',
            events: data.events,
            nextOffset: data.next_offset,
          });
        }
      })
      .catch(() => {
        if (current) {
          setCatalog({
            status: 'error',
            events: [],
            nextOffset: null,
          });
        }
      });

    return () => {
      current = false;
    };
  }, [attempt]);

  const visibleEvents = catalog.events.filter((event) => {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).formatToParts(new Date(event.start));

    const getPart = (type) =>
      parts.find((part) => part.type === type).value;

    const eventDate = `${getPart('year')}-${getPart('month')}-${getPart('day')}`;

    return (
      (category === '' || event.category === category) &&
      (date === '' || eventDate === date)
    );
  });

  function clearFilters() {
    setCategory('');
    setDate('');
  }

  async function loadMore() {
    if (catalog.nextOffset === null || catalog.status !== 'ready') {
      return;
    }

    const nextOffset = catalog.nextOffset;

    setCatalog((previous) => ({
      ...previous,
      status: 'loading-more',
    }));

    try {
      const data = await getEvents(5, nextOffset);

      setCatalog((previous) => {
        const existingIds = new Set(
          previous.events.map((event) => event.id)
        );

        const newEvents = data.events.filter(
          (event) => !existingIds.has(event.id)
        );

        return {
          status: 'ready',
          events: [...previous.events, ...newEvents],
          nextOffset: data.next_offset,
        };
      });
    } catch {
      setCatalog((previous) => ({
        ...previous,
        status: 'load-more-error',
      }));
    }
  }

  return (
    <main id="events" className="dashboard">
      <div className="page-heading">
        <p className="eyebrow">Discover Boston</p>
        <h1>Find your next plan.</h1>
        <p>Browse events, narrow your choices, and plan with a chat.</p>
        <p className="prototype-note">
          Demo: accounts are stored in the project database; the fictional events come from the Python API.
          Ask the chat for events in your own words, then click a result to see its details.
        </p>
      </div>

      <div className="dashboard-grid">
        <EventFeed
          status={catalog.status}
          events={visibleEvents}
          onClearFilters={clearFilters}
          onRetry={() => setAttempt((count) => count + 1)}
          hasMore={catalog.nextOffset !== null}
          onLoadMore={loadMore}
          detailsRequest={detailsRequest}
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
          <ChatPanel onEventSelect={(id) => setDetailsRequest({ id })} />
        </aside>
      </div>
    </main>
  );
}
