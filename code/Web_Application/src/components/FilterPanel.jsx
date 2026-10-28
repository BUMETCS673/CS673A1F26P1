// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; Claude Code (Claude Opus), prompted by Daniel Winnie (date options from API data)
// Overall AI Contribution: ~90%
// AI-Assisted Areas: category/date filter controls
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
// Notes/Verification: manual browser testing on localhost:3000 (desktop and narrow widths)

import React from 'react';

function formatDate(value) {
  return new Date(`${value}T12:00:00`).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
}

export default function FilterPanel({ events, category, date, onCategoryChange, onDateChange, onClear }) {
  // Derive choices from the same catalog shown in the event queue.
  const categories = [...new Set(events.map((event) => event.category))].sort();
  // Events arrive sorted, so the first and last give the date range.
  const firstDate = events[0]?.date;
  const lastDate = events[events.length - 1]?.date;

  return (
    <section className="panel filter-panel" aria-labelledby="filters-title">
      <div className="section-heading">
        <h2 id="filters-title">Filter events</h2>
        <button className="text-button" type="button" onClick={onClear}>Clear</button>
      </div>
      <p className="muted-text">Narrow the event queue by category and date.</p>
      <label htmlFor="event-category">Category</label>
      <select id="event-category" value={category} onChange={(event) => onCategoryChange(event.target.value)}>
        <option value="">All categories</option>
        {categories.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
      </select>
      <label htmlFor="event-date">Date</label>
      <input id="event-date" type="date" value={date} onChange={(event) => onDateChange(event.target.value)} />
      {firstDate && (
        <p className="filter-hint">
          Sample dates: {firstDate === lastDate ? formatDate(firstDate) : `${formatDate(firstDate)} – ${formatDate(lastDate)}`}.
        </p>
      )}
    </section>
  );
}
