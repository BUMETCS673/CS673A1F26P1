// AI-USAGE SUMMARY
// Authors: Junshuo Huang (placeholder view), Daniel Winnie (FV-95 My Plans view, taking over from the Iteration 2 plan)
// Tools: OpenAI Codex, prompted by Junshuo Huang (placeholder); Claude Code (Claude Opus), prompted by Daniel Winnie (FV-95)
// Overall AI Contribution: 100% of the placeholder draft (Junshuo); ~90% of the FV-95 view (Daniel)
// AI-Assisted Areas: My Plans placeholder view (Junshuo); saved events grouped by Boston day with a Past section, remove, and open details (FV-95)
// Human Contributions: Junshuo Huang supplied the team navigation requirements; Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/views/MyPlansView.test.jsx (npm test); browser check with two accounts

import React, { useEffect } from 'react';
import SaveButton from '../components/SaveButton.jsx';
import { bostonDateKey, formatBostonTimeRange, BOSTON_TIME_ZONE } from '../recommendations.js';
import { usePlans } from '../plans.jsx';
import './MyPlansView.css';

const dayHeading = new Intl.DateTimeFormat('en-US', {
  timeZone: BOSTON_TIME_ZONE, weekday: 'long', month: 'long', day: 'numeric', year: 'numeric',
});

// Upcoming plans grouped by the Boston calendar day they start on, in start order.
// The server already sorts by start time.
function groupByBostonDay(plans) {
  const groups = [];
  for (const plan of plans) {
    const key = bostonDateKey(plan.event.start) ?? 'unknown';
    if (groups.at(-1)?.key !== key) {
      const start = new Date(plan.event.start);
      const heading = Number.isNaN(start.getTime()) ? 'Date to be announced' : dayHeading.format(start);
      groups.push({ key, heading, plans: [] });
    }
    groups.at(-1).plans.push(plan);
  }
  return groups;
}

// Upcoming: section (h2) > day (h3) > event (h4). Past: section (h2) > event (h3).
function PlanItem({ plan, onEventSelect, Heading = 'h4' }) {
  const { event } = plan;
  const happeningNow = !plan.ended && new Date(event.start) <= new Date();
  return (
    <li className="panel plan-item">
      <div className="plan-item-text">
        <div className="event-badges">
          <span className="category-badge">{event.category}</span>
          {happeningNow && <span className="placeholder-badge">Happening now</span>}
          {plan.ended && <span className="count-badge">Ended</span>}
        </div>
        <Heading>{event.title}</Heading>
        <p>{formatBostonTimeRange(event.start, event.end)}</p>
        <p>{event.location || 'Location unavailable'}</p>
      </div>
      <div className="plan-item-actions">
        <button
          className="secondary-button"
          type="button"
          aria-label={`View details: ${event.title}`}
          onClick={() => onEventSelect?.(event.id)}
        >
          View details
        </button>
        <SaveButton eventId={event.id} eventTitle={event.title} ended={plan.ended} />
      </div>
    </li>
  );
}

/**
 * Props:
 *   onEventSelect  called with an event ID to show its details on the Events page
 *   onBrowse       called by the empty state's "Browse events" button
 */
export default function MyPlansView({ onEventSelect, onBrowse }) {
  const plans = usePlans();

  // Refresh whenever the page is opened (an event may have ended since).
  const reload = plans?.reload;
  useEffect(() => { reload?.(); }, [reload]);

  if (!plans) return null;

  const upcoming = plans.plans.filter((plan) => !plan.ended);
  // Most recent first: the event that just ended is the one people look for.
  const past = plans.plans.filter((plan) => plan.ended).reverse();
  const unavailable = plans.unavailableCount;

  let content;
  if (plans.status === 'loading' && plans.plans.length === 0) {
    content = <p className="panel">Loading your plans…</p>;
  } else if (plans.status === 'error' && plans.plans.length === 0) {
    content = (
      <div className="panel empty-state">
        <h2 role="alert">Couldn't load your plans</h2>
        <p>Check that the project is running, then try again.</p>
        <button className="secondary-button" type="button" onClick={plans.reload}>Try again</button>
      </div>
    );
  } else if (plans.plans.length === 0) {
    content = (
      <div className="panel empty-state">
        <h2>No plans yet</h2>
        <p>Open an event's details or ask the chat, then choose "Save to My Plans".</p>
        <button className="primary-button" type="button" onClick={onBrowse}>Browse events</button>
      </div>
    );
  } else {
    content = (
      <>
        {plans.status === 'error' && (
          <p className="prototype-note" role="alert">
            Couldn't refresh your plans. This list may be out of date.{' '}
            <button className="text-button" type="button" onClick={plans.reload}>Try again</button>
          </p>
        )}
        <section aria-labelledby="upcoming-plans-title">
          <h2 id="upcoming-plans-title">Upcoming</h2>
          {upcoming.length === 0 ? (
            <p className="muted-text">Nothing upcoming. Your saved events have all ended.</p>
          ) : groupByBostonDay(upcoming).map((group) => (
            <section className="plan-day" key={group.key} aria-label={group.heading}>
              <h3 className="plan-day-heading">{group.heading}</h3>
              <ul className="plan-list">
                {group.plans.map((plan) => (
                  <PlanItem plan={plan} key={plan.event.id} onEventSelect={onEventSelect} />
                ))}
              </ul>
            </section>
          ))}
        </section>
        {past.length > 0 && (
          <section aria-labelledby="past-plans-title" className="plan-past">
            <h2 id="past-plans-title">Past</h2>
            <ul className="plan-list">
              {past.map((plan) => (
                <PlanItem plan={plan} key={plan.event.id} onEventSelect={onEventSelect} Heading="h3" />
              ))}
            </ul>
          </section>
        )}
      </>
    );
  }

  return (
    <main className="dashboard my-plans">
      <header className="page-heading">
        <p className="eyebrow">My Plans</p>
        <h1>Your saved events</h1>
        <p>Times are shown in Boston local time.</p>
      </header>
      {unavailable > 0 && (
        <p className="muted-text plan-unavailable">
          {unavailable === 1
            ? '1 saved event is no longer available, so it is not shown.'
            : `${unavailable} saved events are no longer available, so they are not shown.`}
        </p>
      )}
      <div className="my-plans-content">{content}</div>
    </main>
  );
}
