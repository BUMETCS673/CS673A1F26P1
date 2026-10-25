import React from 'react';

export default function EventFeed({ events, onClearFilters }) {
  return (
    <section className="event-feed" aria-labelledby="events-title">
      <div className="section-heading">
        <div>
          <h2 id="events-title">Boston event queue</h2>
          <p className="muted-text">Fictional showcase listings · times shown in Boston local time</p>
        </div>
        <span className="count-badge" role="status">{events.length} sample {events.length === 1 ? 'event' : 'events'}</span>
      </div>

      {events.length === 0 ? (
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
