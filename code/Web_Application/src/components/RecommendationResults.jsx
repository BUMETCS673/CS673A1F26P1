// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 recommendation results component (event cards, clarification, no matches)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/components/RecommendationResults.test.jsx (npm test); standalone preview at /src/previews/recommendations/

import React from 'react';
import { describeConditions, formatBostonTimeRange, bostonDateKey, resultKind } from '../recommendations.js';
import './RecommendationResults.css';

// Example requests the FV-124 parser understands. Clicking one calls onSuggestion.
export const EXAMPLE_REQUESTS = [
  'music this friday after 6pm',
  'food near North End',
  'something fun tomorrow',
];

function ConditionList({ conditions }) {
  if (conditions.length === 0) return null;
  return (
    <ul className="recommendation-conditions" aria-label="Understood conditions">
      {conditions.map((condition) => <li key={condition}>{condition}</li>)}
    </ul>
  );
}

function Suggestions({ onSuggestion }) {
  if (!onSuggestion) return null;
  return (
    <div className="recommendation-suggestions">
      <p className="muted-text">Try one of these:</p>
      <div>
        {EXAMPLE_REQUESTS.map((example) => (
          <button className="secondary-button" type="button" key={example} onClick={() => onSuggestion(example)}>
            {example}
          </button>
        ))}
      </div>
    </div>
  );
}

// Each card is one button so the whole card is clickable and keyboard reachable.
// It reports only the shared event ID; the details view looks up the rest.
function RecommendationCard({ event, onEventSelect }) {
  return (
    <li>
      <button
        type="button"
        className="recommendation-card"
        onClick={() => onEventSelect?.(event.id)}
        aria-label={`${event.title}. View event details`}
      >
        <span className="recommendation-card-top">
          {event.category && <span className="category-badge">{event.category}</span>}
          <span className="recommendation-card-cta" aria-hidden="true">Details →</span>
        </span>
        <strong className="recommendation-card-title">{event.title}</strong>
        <span className="recommendation-card-line">
          <time dateTime={bostonDateKey(event.start) ?? undefined}>
            {formatBostonTimeRange(event.start, event.end)}
          </time>
        </span>
        {event.location && <span className="recommendation-card-line">{event.location}</span>}
      </button>
    </li>
  );
}

/**
 * Shows the chat's answer to one request: matching event cards, a clarification
 * prompt, or a no-matches message.
 *
 * Props:
 *   response       { interpretation, events } (see src/recommendations.js)
 *   onEventSelect  called with the event ID when a card is clicked
 *   onSuggestion   optional; called with an example request text
 */
export default function RecommendationResults({ response, onEventSelect, onSuggestion }) {
  const kind = resultKind(response);
  const conditions = describeConditions(response?.interpretation);

  if (kind === 'clarification') {
    return (
      <section className="recommendation-results recommendation-message" aria-label="Recommendation results">
        <h3>Could you rephrase that?</h3>
        <p>
          {response?.message ?? "I couldn't tell what kind of event you want. "
            + 'Mention a category (Music, Arts, Food, Outdoors, Social), a day, a time such as '
            + "'after 6pm', or a place such as 'near Fenway'."}
        </p>
        <Suggestions onSuggestion={onSuggestion} />
      </section>
    );
  }

  if (kind === 'no-matches') {
    return (
      <section className="recommendation-results recommendation-message" aria-label="Recommendation results">
        <h3>No matching events</h3>
        <p>{response.message ?? 'No upcoming Boston events match all of these conditions.'}</p>
        <ConditionList conditions={conditions} />
        <p className="muted-text">Try removing a condition, such as the time or place, or pick another day.</p>
        <Suggestions onSuggestion={onSuggestion} />
      </section>
    );
  }

  const count = response.events.length;
  return (
    <section className="recommendation-results" aria-label="Recommendation results">
      <p className="recommendation-summary" role="status">
        {count} {count === 1 ? 'event matches' : 'events match'}
        <span className="muted-text"> · times in Boston local time</span>
      </p>
      <ConditionList conditions={conditions} />
      <ul className="recommendation-list">
        {response.events.map((event) => (
          <RecommendationCard event={event} key={event.id} onEventSelect={onEventSelect} />
        ))}
      </ul>
    </section>
  );
}
