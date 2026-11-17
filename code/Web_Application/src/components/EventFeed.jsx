// AI-USAGE SUMMARY
// Authors: Daniel Winnie, Jibek Kelgenbaeva
// Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; Claude Code (Claude Opus), prompted by Daniel Winnie (loading/error states, opening details from chat cards); ChatGPT (OpenAI GPT-6), prompted by Jibek Kelgenbaeva (FV-122/FV-123)
// Overall AI Contribution: ~90% (Daniel's parts); 90% (Jibek's FV-122/FV-123 parts)
// AI-Assisted Areas: event cards, feed states, Boston-local date/time formatting, event details view, Load More pagination, and empty/error handling; opening details from chat cards (FV-125); Save to My Plans on cards and details (FV-95); friends going line in details
// Human Contributions: Daniel Winnie: requirements, design choices, original implementation, and review; Jibek Kelgenbaeva: FV-122/FV-123 requirements, integration, testing, and verification
// Notes/Verification: FV-122/FV-123 backend tests and manual browser verification; desktop and narrow-width checks from earlier implementation

import React, { useEffect, useRef, useState } from 'react';
import { getEventById } from '../api.js';
import SaveButton from './SaveButton.jsx';
import FriendsGoing from './FriendsGoing.jsx';

const BOSTON_TIMEZONE = 'America/New_York';

function formatBostonDate(value) {
  if (!value) return 'unavailable';

  return new Intl.DateTimeFormat('en-US', {
    timeZone: BOSTON_TIMEZONE,
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value));
}

function formatBostonTime(value) {
  if (!value) return 'unavailable';

  return new Intl.DateTimeFormat('en-US', {
    timeZone: BOSTON_TIMEZONE,
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(new Date(value));
}

export default function EventFeed({
  status,
  events,
  onClearFilters,
  onRetry,
  hasMore,
  onLoadMore,
  detailsRequest,
}) {
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsError, setDetailsError] = useState('');
  const detailsPanel = useRef(null);
  const latestRequest = useRef(0);

  // FV-125: a chat result card opens the same details view by event ID.
  useEffect(() => {
    if (!detailsRequest) return;
    openDetails(detailsRequest.id).then(() => {
      detailsPanel.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
    });
  }, [detailsRequest]);

  async function openDetails(eventId) {
    // Only the most recent click may fill the panel, if two answers arrive out of order.
    const requestNumber = ++latestRequest.current;
    setSelectedEvent(null);
    setDetailsError('');
    setDetailsLoading(true);

    try {
      const event = await getEventById(eventId);
      if (requestNumber === latestRequest.current) setSelectedEvent(event);
    } catch (error) {
      if (requestNumber === latestRequest.current) {
        setDetailsError(error.status === 404
          ? 'This event is no longer available.'
          : "Couldn't load event details.");
      }
    } finally {
      if (requestNumber === latestRequest.current) setDetailsLoading(false);
    }
  }

  return (
    <section className="event-feed" aria-labelledby="events-title">
      <div className="section-heading">
        <div>
          <h2 id="events-title">Boston event queue</h2>
          <p className="muted-text">
            Fictional showcase listings · times shown in Boston local time
          </p>
        </div>

        <span className="count-badge" role="status">
          {status === 'loading'
            ? 'Loading…'
            : status === 'error'
              ? 'Unavailable'
              : `${events.length} events`}
        </span>
      </div>

      {status === 'loading' ? (
        <div className="panel empty-state">
          <p>Loading events from the server…</p>
        </div>
      ) : status === 'error' ? (
        <div className="panel empty-state">
          <h3 role="alert">Couldn't load events</h3>
          <p>Check that the Python backend is running, then try again.</p>
          <button
            className="secondary-button"
            type="button"
            onClick={onRetry}
          >
            Try again
          </button>
        </div>
      ) : (
        <>
          {events.length === 0 ? (
            <div className="panel empty-state">
              <h3>No upcoming events</h3>
              <p>Try another category or date, or clear the filters.</p>
              <button
                className="secondary-button"
                type="button"
                onClick={onClearFilters}
              >
                Clear filters
              </button>
            </div>
          ) : (
            <div className="event-list">
              {events.map((event) => (
                <article className="panel event-card" key={event.id}>
                  <div className="event-date" aria-hidden="true">
                    <span>
                      {new Intl.DateTimeFormat('en-US', {
                        timeZone: BOSTON_TIMEZONE,
                        month: 'short',
                      }).format(new Date(event.start))}
                    </span>
                    <strong>
                      {new Intl.DateTimeFormat('en-US', {
                        timeZone: BOSTON_TIMEZONE,
                        day: 'numeric',
                      }).format(new Date(event.start))}
                    </strong>
                  </div>

                  <div className="event-content">
                    <div className="event-badges">
                      <span className="category-badge">
                        {event.category || 'unavailable'}
                      </span>
                      <span className="muted-text">Sample listing</span>
                    </div>

                    <h3>{event.title}</h3>

                    <p>
                      {formatBostonDate(event.start)}
                      {' · '}
                      {formatBostonTime(event.start)}
                    </p>

                    <p>{event.location || 'unavailable'}</p>

                    <div className="event-actions">
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => openDetails(event.id)}
                      >
                        View details
                      </button>
                      <SaveButton eventId={event.id} eventTitle={event.title} />
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {hasMore && (
            <div className="empty-state">
              <button
                className="secondary-button"
                type="button"
                onClick={onLoadMore}
                disabled={status === 'loading-more'}
              >
                {status === 'loading-more' ? 'Loading more…' : 'Load More'}
              </button>

              {status === 'load-more-error' && (
                <p role="alert">
                  Couldn't load more events. Please try again.
                </p>
              )}
            </div>
          )}
        </>
      )}

      {(selectedEvent || detailsLoading || detailsError) && (
        <div className="panel" aria-live="polite" ref={detailsPanel}>
          <button
            className="secondary-button"
            type="button"
            onClick={() => {
              setSelectedEvent(null);
              setDetailsError('');
            }}
          >
            Close details
          </button>

          {detailsLoading && <p>Loading event details…</p>}
          {detailsError && <p role="alert">{detailsError}</p>}

          {selectedEvent && (
            <div>
              <h3>{selectedEvent.title || 'unavailable'}</h3>
              <p><strong>Category:</strong> {selectedEvent.category || 'unavailable'}</p>
              <p><strong>Location:</strong> {selectedEvent.location || 'unavailable'}</p>
              <p><strong>Date:</strong> {formatBostonDate(selectedEvent.start)}</p>
              <p><strong>Start:</strong> {formatBostonTime(selectedEvent.start)}</p>
              <p><strong>End:</strong> {formatBostonTime(selectedEvent.end)}</p>
              <p><strong>Description:</strong> {selectedEvent.description || 'unavailable'}</p>
              <FriendsGoing eventId={selectedEvent.id} />
              <SaveButton
                eventId={selectedEvent.id}
                eventTitle={selectedEvent.title}
                ended={new Date(selectedEvent.end) <= new Date()}
              />
            </div>
          )}
        </div>
      )}
    </section>
  );
}
