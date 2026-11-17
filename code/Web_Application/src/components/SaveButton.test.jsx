// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: Save to My Plans button tests (FV-95)
// Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
// Notes/Verification: npm test

import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import SaveButton from './SaveButton.jsx';
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

function renderButtons(...buttons) {
  return render(<PlansProvider>{buttons}</PlansProvider>);
}
const saveButton = (title = 'Acoustic evening in Back Bay') =>
  screen.findByRole('button', { name: `Save to My Plans: ${title}` });
const removeButton = (title = 'Acoustic evening in Back Bay') =>
  screen.findByRole('button', { name: `Remove from My Plans: ${title}` });
const plansLoaded = () => waitFor(() => expect(backend.callsTo('GET', '/api/plans').length).toBeGreaterThan(0));

describe('SaveButton', () => {
  it('renders nothing outside a PlansProvider', () => {
    const { container } = render(<SaveButton eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    expect(container.innerHTML).toBe('');
  });

  it('saves the event, then offers to remove it', async () => {
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    await plansLoaded();
    fireEvent.click(await saveButton());

    expect(await removeButton()).toBeTruthy();
    expect(screen.getByText('✓ In My Plans')).toBeTruthy();
    expect(backend.callsTo('PUT', '/api/plans/sample-1')).toHaveLength(1);
    expect(backend.savedIds(1)).toEqual(['sample-1']);
  });

  it('shows an event saved earlier as already in My Plans', async () => {
    backend.plans.set(1, new Map([['sample-1', '2026-11-17T09:00:00Z']]));
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    expect(await removeButton()).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Save to My Plans/ })).toBeNull();
  });

  it('removes a saved event', async () => {
    backend.plans.set(1, new Map([['sample-1', '2026-11-17T09:00:00Z']]));
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    fireEvent.click(await removeButton());
    expect(await saveButton()).toBeTruthy();
    expect(backend.savedIds(1)).toEqual([]);
  });

  it('disables the button while saving, so a double click sends one request', async () => {
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    await plansLoaded();
    const release = backend.hold('PUT', '/api/plans/sample-1');
    const button = await saveButton();
    fireEvent.click(button);
    fireEvent.click(button);
    await waitFor(() => expect(button.disabled).toBe(true));
    expect(button.textContent).toBe('Saving…');
    await act(async () => release());
    expect(await removeButton()).toBeTruthy();
    expect(backend.callsTo('PUT', '/api/plans/sample-1')).toHaveLength(1);
  });

  it("shows the server's reason when saving fails and stays unsaved", async () => {
    backend.events.find((event) => event.id === 'sample-1').end = '2026-11-17T11:00:00-05:00';
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    await plansLoaded();
    fireEvent.click(await saveButton());
    expect((await screen.findByRole('alert')).textContent).toBe('This event has already ended.');
    expect(screen.getByRole('button', { name: /Save to My Plans/ }).disabled).toBe(false);
  });

  it('explains a network failure and lets the person try again', async () => {
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    await plansLoaded();
    backend.failNext('PUT', '/api/plans/sample-1', 'network');
    fireEvent.click(await saveButton());
    expect((await screen.findByRole('alert')).textContent).toMatch(/Could not reach the server/);
    fireEvent.click(await saveButton());
    expect(await removeButton()).toBeTruthy();
    expect(screen.queryByRole('alert')).toBeNull();
  });

  it('a failed removal keeps the event saved and says why', async () => {
    backend.plans.set(1, new Map([['sample-1', '2026-11-17T09:00:00Z']]));
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    backend.failNext('DELETE', '/api/plans/sample-1', 503);
    fireEvent.click(await removeButton());
    expect((await screen.findByRole('alert')).textContent).toBe('Simulated 503 failure.');
    expect(await removeButton()).toBeTruthy();
    expect(backend.savedIds(1)).toEqual(['sample-1']);
  });

  it('an ended event shows a note instead of a Save button', async () => {
    renderButtons(<SaveButton key="a" eventId="past-1" eventTitle="Last week gallery night" ended />);
    await plansLoaded();
    expect(screen.getByText('This event has ended.')).toBeTruthy();
    expect(screen.queryByRole('button')).toBeNull();
  });

  it('an ended event that was saved can still be removed', async () => {
    backend.plans.set(1, new Map([['past-1', '2026-11-01T09:00:00Z']]));
    renderButtons(<SaveButton key="a" eventId="past-1" eventTitle="Last week gallery night" ended />);
    fireEvent.click(await removeButton('Last week gallery night'));
    expect(await screen.findByText('This event has ended.')).toBeTruthy();
    expect(backend.savedIds(1)).toEqual([]);
  });

  it('keeps every button for the same event in sync', async () => {
    renderButtons(
      <SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />,
      <SaveButton key="b" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />,
      <SaveButton key="c" eventId="sample-3" eventTitle="North End food walk" />,
    );
    await plansLoaded();
    fireEvent.click((await screen.findAllByRole('button', { name: 'Save to My Plans: Acoustic evening in Back Bay' }))[0]);
    await waitFor(() => expect(screen.getAllByRole('button', { name: /Remove from My Plans: Acoustic/ })).toHaveLength(2));
    expect(await saveButton('North End food walk')).toBeTruthy();
  });

  it('encodes event IDs in the request URL', async () => {
    backend.events.push({ ...backend.events[0], id: 'odd id/?#' });
    renderButtons(<SaveButton key="a" eventId="odd id/?#" eventTitle="Odd" />);
    await plansLoaded();
    fireEvent.click(await saveButton('Odd'));
    expect(await removeButton('Odd')).toBeTruthy();
    expect(fetch.mock.calls.some(([url]) => url === '/api/plans/odd%20id%2F%3F%23')).toBe(true);
  });

  it('a removal is not undone by a slow refresh that started before it', async () => {
    renderButtons(<SaveButton key="a" eventId="sample-1" eventTitle="Acoustic evening in Back Bay" />);
    await plansLoaded();
    // The refresh after saving is held, so it answers after the removal.
    const release = backend.hold('GET', '/api/plans');
    fireEvent.click(await saveButton());
    fireEvent.click(await removeButton());
    await waitFor(() => expect(backend.savedIds(1)).toEqual([]));
    await act(async () => release());
    await waitFor(() => expect(backend.callsTo('GET', '/api/plans').length).toBeGreaterThanOrEqual(3));
    expect(await saveButton()).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Remove from My Plans/ })).toBeNull();
  });
});
