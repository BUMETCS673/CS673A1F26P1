// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 helper unit tests
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: npm test

import { describe, expect, it } from 'vitest';
import { bostonDateKey, describeConditions, formatBostonTimeRange, resultKind } from './recommendations.js';

describe('resultKind', () => {
  it('asks for clarification when the parser could not read the request', () => {
    expect(resultKind({ interpretation: { needs_clarification: true }, events: [] })).toBe('clarification');
  });

  it('treats a missing response as needing clarification', () => {
    expect(resultKind(undefined)).toBe('clarification');
  });

  it('reports no matches for an understood request with no events', () => {
    expect(resultKind({ interpretation: { needs_clarification: false }, events: [] })).toBe('no-matches');
    expect(resultKind({ interpretation: { needs_clarification: false } })).toBe('no-matches');
  });

  it('shows results when events are present', () => {
    expect(resultKind({ interpretation: { needs_clarification: false }, events: [{ id: 'a' }] })).toBe('results');
  });

  it('prefers clarification even if events were sent', () => {
    expect(resultKind({ interpretation: { needs_clarification: true }, events: [{ id: 'a' }] })).toBe('clarification');
  });
});

describe('formatBostonTimeRange', () => {
  it('formats a same-day range in Boston time', () => {
    expect(formatBostonTimeRange('2026-11-13T19:30:00-05:00', '2026-11-13T22:00:00-05:00'))
      .toBe('Fri, Nov 13 · 7:30 PM – 10:00 PM');
  });

  it('converts UTC input to Boston local time', () => {
    // 00:30 UTC on Nov 14 is still 7:30 PM on Nov 13 in Boston (EST, UTC-5).
    expect(formatBostonTimeRange('2026-11-14T00:30:00Z', '2026-11-14T03:00:00Z'))
      .toBe('Fri, Nov 13 · 7:30 PM – 10:00 PM');
  });

  it('uses daylight time before the November switch', () => {
    expect(formatBostonTimeRange('2026-10-15T22:00:00Z')).toBe('Thu, Oct 15 · 6:00 PM');
  });

  it('shows the end date when an event ends on a later day', () => {
    expect(formatBostonTimeRange('2026-11-13T21:00:00-05:00', '2026-11-14T01:00:00-05:00'))
      .toBe('Fri, Nov 13 · 9:00 PM – Sat, Nov 14 · 1:00 AM');
  });

  it('omits a missing, unreadable, or earlier end time', () => {
    expect(formatBostonTimeRange('2026-11-13T19:30:00-05:00')).toBe('Fri, Nov 13 · 7:30 PM');
    expect(formatBostonTimeRange('2026-11-13T19:30:00-05:00', 'soon')).toBe('Fri, Nov 13 · 7:30 PM');
    expect(formatBostonTimeRange('2026-11-13T19:30:00-05:00', '2026-11-13T18:00:00-05:00'))
      .toBe('Fri, Nov 13 · 7:30 PM');
  });

  it('falls back when the start time is unreadable', () => {
    expect(formatBostonTimeRange('not a date')).toBe('Time to be announced');
    expect(formatBostonTimeRange(undefined)).toBe('Time to be announced');
    expect(formatBostonTimeRange(null)).toBe('Time to be announced');
  });
});

describe('bostonDateKey', () => {
  it('returns the Boston calendar date', () => {
    expect(bostonDateKey('2026-11-14T03:00:00Z')).toBe('2026-11-13');
    expect(bostonDateKey('2026-11-14T06:00:00Z')).toBe('2026-11-14');
  });

  it('returns null for unreadable input', () => {
    expect(bostonDateKey('nope')).toBeNull();
  });
});

describe('describeConditions', () => {
  const parsed = (fields) => ({
    category: null, date: null, time: null, time_operator: null,
    location: null, location_operator: null, timezone: 'America/New_York',
    needs_clarification: false, ...fields,
  });

  it('describes every parser field in reading order', () => {
    expect(describeConditions(parsed({
      category: 'Music', date: '2026-11-13', time: '18:00', time_operator: 'after',
      location: 'Fenway', location_operator: 'near',
    }))).toEqual(['Music', 'Fri, Nov 13', 'after 6:00 PM', 'near Fenway']);
  });

  it('formats morning, noon, and midnight times', () => {
    expect(describeConditions(parsed({ time: '07:05', time_operator: 'at' }))).toEqual(['at 7:05 AM']);
    expect(describeConditions(parsed({ time: '12:00', time_operator: 'before' }))).toEqual(['before 12:00 PM']);
    expect(describeConditions(parsed({ time: '00:00', time_operator: 'after' }))).toEqual(['after 12:00 AM']);
  });

  it('returns nothing for clarification or missing input', () => {
    expect(describeConditions({ needs_clarification: true, category: 'Music' })).toEqual([]);
    expect(describeConditions(undefined)).toEqual([]);
  });

  it('defaults missing operators', () => {
    expect(describeConditions(parsed({ time: '18:00', location: 'Allston' }))).toEqual(['at 6:00 PM', 'in Allston']);
  });
});
