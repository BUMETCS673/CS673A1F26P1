import React from 'react';

export default function EventFeed({ status, events, onClearFilters, onRetry }) {
  return (
    <section className="event-feed" aria-labelledby="events-title">
      <div className="section-heading">
        <div>
          <h2 id="events-title">Boston event queue</h2>
          <p className="muted-text">Fictional showcase listings · times shown in Boston local time</p>
        </div>
        <span className="count-badge" role="status">
          {status === 'ready' ? `${events.length} sample ${events.length === 1 ? 'event' : 'events'}`
            : status === 'error' ? 'Unavailable' : 'Loading…'}
        </span>
      </div>

      {status === 'loading' ? (
        <div className="panel empty-state"><p>Loading events from the server…</p></div>
      ) : status === 'error' ? (
        <div className="panel empty-state">
          <h3 role="alert">Could not load events.</h3>
          <p>Check that the Python backend is running, then try again.</p>
          <button className="secondary-button" type="button" onClick={onRetry}>Try again</button>
        </div>
      ) : events.length === 0 ? (
        <div className="panel empty-state">
          <h3>No sample events match.</h3>
          <p>Try another category or date, or clear the sample filters.</p>
          <button className="secondary-button" type="button" onClick={onClearFilters}>Clear filters</button>
        </div>
      ) : (
        <div className="event-list">
          {events.map((event) => (
            <article className="panel event-card" key={event.id}>
              <div className="event-date" aria-hidden="true">
                <span>{new Date(`${event.date}T12:00:00`).toLocaleDateString('en-US', { month: 'short' })}</span>
                <strong>{Number(event.date.slice(-2))}</strong>
              </div>
              <div className="event-content">
                <div className="event-badges">
                  <span className="category-badge">{event.category}</span>
                  <span className="muted-text">Sample listing</span>
                </div>
                <h3>{event.title}</h3>
                <p><time dateTime={event.date}>{event.date}</time> · {event.time}</p>
                <p>{event.location}</p>
                <details>
                  <summary>View sample details</summary>
                  <p>{event.description}</p>
                </details>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
