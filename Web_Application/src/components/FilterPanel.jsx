import React from 'react';
import { sampleEvents } from '../sampleEvents.js';

// Derive choices from the same sample catalog used by the event queue.
const categories = [...new Set(sampleEvents.map((event) => event.category))].sort();

export default function FilterPanel({ category, date, onCategoryChange, onDateChange, onClear }) {
  return (
    <section className="panel filter-panel" aria-labelledby="filters-title">
      <div className="section-heading">
        <h2 id="filters-title">Filter events</h2>
        <button className="text-button" type="button" onClick={onClear}>Clear</button>
      </div>
      <p className="muted-text">Sample filters only. Real event filtering will connect here later.</p>
      <label htmlFor="event-category">Category</label>
      <select id="event-category" value={category} onChange={(event) => onCategoryChange(event.target.value)}>
        <option value="">All categories</option>
        {categories.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
      </select>
      <label htmlFor="event-date">Date</label>
      <input id="event-date" type="date" value={date} onChange={(event) => onDateChange(event.target.value)} />
      <p className="filter-hint">Sample dates: November 1–3, 2026.</p>
    </section>
  );
}
