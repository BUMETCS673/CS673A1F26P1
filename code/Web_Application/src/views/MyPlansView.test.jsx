// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: My Plans view tests (FV-95)
// Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
// Notes/Verification: npm test

import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import MyPlansView from './MyPlansView.jsx';
import { PlansProvider } from '../plans.jsx';
import { createBackend, NOW } from '../testSupport/fakeBackend.js';

let backend;
beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(NOW);
  backend = createBackend();
  backend.signedIn = 1;
  vi.stubGlobal('fetch', vi.fn(backend.fetch));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

function saved(...ids) {
  backend.plans.set(1, new Map(ids.map((id, index) => [id, `2026-11-10T0${index}:00:00Z`])));
}
function renderView(props = {}) {
  return render(<PlansProvider><MyPlansView {...props} /></PlansProvider>);
}
// Event titles only (not the day headings), in the order shown.
const titlesIn = (element) => [...element.querySelectorAll('.plan-item-text > :is(h3, h4)')]
  .map((heading) => heading.textContent);

describe('MyPlansView', () => {
  it('shows an empty state that leads back to the events', async () => {
    const onBrowse = vi.fn();
    renderView({ onBrowse });
    expect(screen.getByText('Loading your plans…')).toBeTruthy();
    expect(await screen.findByRole('heading', { name: 'No plans yet' })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Browse events' }));
    expect(onBrowse).toHaveBeenCalledOnce();
  });

  it('groups upcoming plans by Boston day, in start order', async () => {
    saved('sample-4', 'sample-3', 'sample-2', 'sample-1');
    renderView();
    const saturday = await screen.findByRole('region', { name: 'Saturday, November 21, 2026' });
    // 11:30 PM Boston is Nov 22 in UTC, but it still belongs to Saturday.
    expect(titlesIn(saturday)).toEqual(['Acoustic evening in Back Bay', 'Late jazz in the South End']);
    expect(titlesIn(screen.getByRole('region', { name: 'Sunday, November 22, 2026' })))
      .toEqual(['North End food walk']);
    expect(titlesIn(screen.getByRole('region', { name: 'Saturday, December 5, 2026' })))
      .toEqual(['Harbor sunrise run']);
    const dayOrder = screen.getAllByRole('heading', { level: 3 }).map((heading) => heading.textContent);
    expect(dayOrder).toEqual(['Saturday, November 21, 2026', 'Sunday, November 22, 2026', 'Saturday, December 5, 2026']);
    expect(screen.queryByRole('heading', { name: 'Past' })).toBeNull();
  });

  it('shows Boston times, the end time on a later day, and a missing location', async () => {
    saved('sample-2', 'sample-4');
    renderView();
    expect(await screen.findByText('Sat, Nov 21 · 11:30 PM – Sun, Nov 22 · 1:00 AM')).toBeTruthy();
    expect(screen.getByText('Location unavailable')).toBeTruthy();
  });

  it('puts ended plans under Past, most recent first', async () => {
    saved('past-1', 'sample-1', 'past-2');
    renderView();
    const past = (await screen.findByRole('heading', { name: 'Past' })).closest('section');
    expect(titlesIn(past)).toEqual(['Yesterday board games', 'Last week gallery night']);
    expect(within(past).getAllByText('Ended')).toHaveLength(2);
    const upcoming = screen.getByRole('heading', { name: 'Upcoming' }).closest('section');
    expect(titlesIn(upcoming)).toEqual(['Acoustic evening in Back Bay']);
    // An ended plan can be removed but not saved again.
    expect(within(past).getAllByRole('button', { name: /Remove from My Plans/ })).toHaveLength(2);
  });

  it('says so when every saved event has ended', async () => {
    saved('past-1');
    renderView();
    expect(await screen.findByText('Nothing upcoming. Your saved events have all ended.')).toBeTruthy();
  });

  it('marks an event that has started but not ended as happening now', async () => {
    vi.setSystemTime(new Date('2026-11-21T18:30:00-05:00'));
    saved('sample-1', 'sample-2');
    renderView();
    const item = (await screen.findByRole('heading', { name: 'Acoustic evening in Back Bay' })).closest('li');
    expect(within(item).getByText('Happening now')).toBeTruthy();
    const later = screen.getByRole('heading', { name: 'Late jazz in the South End' }).closest('li');
    expect(within(later).queryByText('Happening now')).toBeNull();
  });

  it('removes a plan immediately when Remove is clicked', async () => {
    saved('sample-1', 'sample-3');
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: 'Remove from My Plans: Acoustic evening in Back Bay' }));
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Acoustic evening in Back Bay' })).toBeNull());
    expect(screen.getByRole('heading', { name: 'North End food walk' })).toBeTruthy();
    expect(backend.savedIds(1)).toEqual(['sample-3']);
  });

  it('removing the last plan shows the empty state', async () => {
    saved('sample-1');
    renderView();
    fireEvent.click(await screen.findByRole('button', { name: /Remove from My Plans/ }));
    expect(await screen.findByRole('heading', { name: 'No plans yet' })).toBeTruthy();
  });

  it('View details reports the event ID', async () => {
    saved('sample-3');
    const onEventSelect = vi.fn();
    renderView({ onEventSelect });
    fireEvent.click(await screen.findByRole('button', { name: 'View details: North End food walk' }));
    expect(onEventSelect).toHaveBeenCalledWith('sample-3');
  });

  it('counts saved events that are no longer in the catalog', async () => {
    saved('sample-1', 'gone-1');
    renderView();
    expect(await screen.findByText('1 saved event is no longer available, so it is not shown.')).toBeTruthy();
    cleanup();
    saved('gone-1', 'gone-2');
    renderView();
    expect(await screen.findByText('2 saved events are no longer available, so they are not shown.')).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'No plans yet' })).toBeTruthy();
  });

  it('offers Try again when the plans cannot be loaded', async () => {
    saved('sample-1');
    // Both the provider and the opened page load the list; fail both.
    backend.failNext('GET', '/api/plans', 503, 2);
    renderView();
    expect((await screen.findByRole('alert')).textContent).toBe("Couldn't load your plans");
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }));
    expect(await screen.findByRole('heading', { name: 'Acoustic evening in Back Bay' })).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('keeps showing the list when only a refresh fails', async () => {
    saved('sample-1');
    const { rerender } = renderView();
    expect(await screen.findByRole('heading', { name: 'Acoustic evening in Back Bay' })).toBeTruthy();
    backend.failNext('GET', '/api/plans', 'network');
    // Opening the page again refreshes it.
    rerender(<PlansProvider><div /></PlansProvider>);
    rerender(<PlansProvider><MyPlansView /></PlansProvider>);
    expect((await screen.findByRole('alert')).textContent).toMatch(/Couldn't refresh your plans/);
    expect(screen.getByRole('heading', { name: 'Acoustic evening in Back Bay' })).toBeTruthy();
  });

  it('shows titles with markup as plain text', async () => {
    backend.events.push({ ...backend.events[0], id: 'xss', title: '<img src=x onerror=alert(1)>' });
    saved('xss');
    const { container } = renderView();
    expect(await screen.findByRole('heading', { name: '<img src=x onerror=alert(1)>' })).toBeTruthy();
    expect(container.querySelector('img')).toBeNull();
  });
});
