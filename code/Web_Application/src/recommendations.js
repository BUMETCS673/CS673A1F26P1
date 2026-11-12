// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 recommendation result helpers (result kind, Boston time formatting, condition summary)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/recommendations.test.js (npm test)

// Plain functions used by RecommendationResults.jsx. They contain no React code,
// so they are easy to test and reuse once the real chat API is connected.
//
// Expected chat response (proposal for the integration step, FV-125):
//   {
//     interpretation: { ...the FV-124 parser fields, e.g. category, date, time,
//                       time_operator, location, location_operator, timezone,
//                       needs_clarification },
//     events: [{ id, title, category, start, end, location, description }]
//   }
// Event `start`/`end` are ISO 8601 times with a UTC offset, the same shape as the
// FV-122/FV-123 catalog fixtures. Only `id` is passed back when a card is clicked.

export const BOSTON_TIME_ZONE = 'America/New_York';

// Which of the three views to show: 'clarification', 'no-matches', or 'results'.
export function resultKind(response) {
  if (!response || response.interpretation?.needs_clarification) return 'clarification';
  return Array.isArray(response.events) && response.events.length > 0 ? 'results' : 'no-matches';
}

const dateFormat = new Intl.DateTimeFormat('en-US', {
  timeZone: BOSTON_TIME_ZONE, weekday: 'short', month: 'short', day: 'numeric',
});
const timeFormat = new Intl.DateTimeFormat('en-US', {
  timeZone: BOSTON_TIME_ZONE, hour: 'numeric', minute: '2-digit',
});

function parseMoment(value) {
  // new Date(null) is 1970-01-01, so accept only non-empty strings.
  if (typeof value !== 'string' || !value) return null;
  const moment = new Date(value);
  return Number.isNaN(moment.getTime()) ? null : moment;
}

// The calendar date (YYYY-MM-DD) of a moment in Boston, for <time dateTime>.
export function bostonDateKey(value) {
  const moment = parseMoment(value);
  if (!moment) return null;
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: BOSTON_TIME_ZONE, year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(moment).map(({ type, value: part }) => [type, part]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}

// "Sat, Nov 14 · 7:00 PM – 9:30 PM" in Boston local time, whatever the viewer's zone.
// An event ending on a later Boston day shows that end date too.
export function formatBostonTimeRange(start, end) {
  const startMoment = parseMoment(start);
  if (!startMoment) return 'Time to be announced';
  const startText = `${dateFormat.format(startMoment)} · ${timeFormat.format(startMoment)}`;
  const endMoment = parseMoment(end);
  if (!endMoment || endMoment <= startMoment) return startText;
  const sameDay = bostonDateKey(start) === bostonDateKey(end);
  const endText = sameDay ? timeFormat.format(endMoment)
    : `${dateFormat.format(endMoment)} · ${timeFormat.format(endMoment)}`;
  return `${startText} – ${endText}`;
}

// "18:30" (parser output) -> "6:30 PM".
function formatClock(value) {
  const match = /^(\d{2}):(\d{2})$/.exec(value ?? '');
  if (!match) return value;
  const hour = Number(match[1]);
  return `${hour % 12 || 12}:${match[2]} ${hour < 12 ? 'AM' : 'PM'}`;
}

// "2026-11-14" -> "Sat, Nov 14" (a calendar date, so it is formatted at noon UTC).
function formatCalendarDate(value) {
  const moment = /^\d{4}-\d{2}-\d{2}$/.test(value ?? '') ? new Date(`${value}T12:00:00Z`) : null;
  if (!moment || Number.isNaN(moment.getTime())) return value;
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC', weekday: 'short', month: 'short', day: 'numeric',
  }).format(moment);
}

// Short phrases describing what the parser understood, e.g. ["Music", "Sat, Nov 14",
// "after 6:00 PM", "near Fenway"]. Empty when nothing was understood.
export function describeConditions(interpretation) {
  if (!interpretation || interpretation.needs_clarification) return [];
  const conditions = [];
  if (interpretation.category) conditions.push(interpretation.category);
  if (interpretation.date) conditions.push(formatCalendarDate(interpretation.date));
  if (interpretation.time) {
    conditions.push(`${interpretation.time_operator ?? 'at'} ${formatClock(interpretation.time)}`);
  }
  if (interpretation.location) {
    conditions.push(`${interpretation.location_operator ?? 'in'} ${interpretation.location}`);
  }
  return conditions;
}
