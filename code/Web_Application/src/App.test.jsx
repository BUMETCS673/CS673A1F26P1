// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: whole-app flows clicked through like a person would (FV-95 My Plans onward)
// Human Contributions: Daniel Winnie: requirements and prompts, chose the flows, reviewed every change before committing
// Notes/Verification: npm test; the same flows were also run in a real browser against the running project

import React from 'react';
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import App from './App.jsx';
import { createBackend, NOW } from './testSupport/fakeBackend.js';

let backend;

beforeAll(() => {
  // jsdom has no native modal dialogs; the real browser checks cover them.
  HTMLDialogElement.prototype.showModal ??= function showModal() { this.open = true; };
  HTMLDialogElement.prototype.close ??= function close() { this.open = false; };
  Element.prototype.scrollIntoView ??= () => {};
});
beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(NOW);
  backend = createBackend();
  vi.stubGlobal('fetch', vi.fn(backend.fetch));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

async function logIn(username) {
  const dialog = await screen.findByRole('dialog', { hidden: true });
  // The dialog's contents are only accessible once it has opened.
  await waitFor(() => expect(dialog.open).toBe(true));
  fireEvent.change(within(dialog).getByLabelText('Username'), { target: { value: username } });
  fireEvent.change(within(dialog).getByLabelText('Password'), { target: { value: `${username} password` } });
  fireEvent.click(within(dialog).getByRole('button', { name: 'Log In' }));
  await screen.findByText(`Signed in as`, { exact: false });
  await waitFor(() => expect(screen.queryByRole('dialog', { hidden: true })).toBeNull());
}
async function logOut() {
  fireEvent.click(screen.getByRole('button', { name: 'Log Out' }));
  await screen.findByRole('dialog', { hidden: true });
}
const goTo = (page) => fireEvent.click(within(screen.getByRole('navigation', { name: 'Main menu' }))
  .getByRole('button', { name: page }));
const eventsPage = () => document.getElementById('events');
const myPlansPage = () => document.querySelector('.my-plans');

describe('My Plans in the whole app', () => {
  it('saves from the event list, shows it in My Plans, and opens its details from there', async () => {
    render(<App />);
    await logIn('alex');
    const card = (await within(eventsPage()).findByRole('heading', { name: 'North End food walk' })).closest('article');
    fireEvent.click(within(card).getByRole('button', { name: 'Save to My Plans: North End food walk' }));
    expect(await within(card).findByText('✓ In My Plans')).toBeTruthy();

    goTo('My Plans');
    const page = myPlansPage();
    expect(await within(page).findByRole('heading', { name: 'North End food walk' })).toBeTruthy();
    expect(within(page).getByRole('region', { name: 'Sunday, November 22, 2026' })).toBeTruthy();

    fireEvent.click(within(page).getByRole('button', { name: 'View details: North End food walk' }));
    // Back on Events, with the details panel open for that event.
    await waitFor(() => expect(eventsPage().closest('[hidden]')).toBeNull());
    const details = (await within(eventsPage()).findByRole('button', { name: 'Close details' })).closest('.panel');
    expect(await within(details).findByText('North End food walk')).toBeTruthy();
    expect(within(details).getByText('✓ In My Plans')).toBeTruthy();
  });

  it('removing in the details view updates the event card and My Plans', async () => {
    backend.plans.set(1, new Map([['sample-1', '2026-11-16T09:00:00Z']]));
    render(<App />);
    await logIn('alex');
    const card = (await within(eventsPage()).findByRole('heading', { name: 'Acoustic evening in Back Bay' })).closest('article');
    expect(await within(card).findByText('✓ In My Plans')).toBeTruthy();
    fireEvent.click(within(card).getByRole('button', { name: 'View details' }));
    const details = (await within(eventsPage()).findByRole('button', { name: 'Close details' })).closest('.panel');
    fireEvent.click(await within(details).findByRole('button', { name: 'Remove from My Plans: Acoustic evening in Back Bay' }));

    expect(await within(card).findByRole('button', { name: 'Save to My Plans: Acoustic evening in Back Bay' })).toBeTruthy();
    goTo('My Plans');
    expect(await within(myPlansPage()).findByRole('heading', { name: 'No plans yet' })).toBeTruthy();
    fireEvent.click(within(myPlansPage()).getByRole('button', { name: 'Browse events' }));
    await waitFor(() => expect(eventsPage().closest('[hidden]')).toBeNull());
  });

  it('keeps plans after signing out and back in, and never shows them to another account', async () => {
    render(<App />);
    await logIn('alex');
    const card = (await within(eventsPage()).findByRole('heading', { name: 'Harbor sunrise run' })).closest('article');
    fireEvent.click(within(card).getByRole('button', { name: /Save to My Plans/ }));
    await within(card).findByText('✓ In My Plans');
    await logOut();

    await logIn('sam');
    const samCard = (await within(eventsPage()).findByRole('heading', { name: 'Harbor sunrise run' })).closest('article');
    await waitFor(() => expect(backend.callsTo('GET', '/api/plans').length).toBeGreaterThanOrEqual(2));
    expect(within(samCard).getByRole('button', { name: /Save to My Plans/ })).toBeTruthy();
    goTo('My Plans');
    expect(await within(myPlansPage()).findByRole('heading', { name: 'No plans yet' })).toBeTruthy();
    await logOut();

    await logIn('alex');
    goTo('My Plans');
    expect(await within(myPlansPage()).findByRole('heading', { name: 'Harbor sunrise run' })).toBeTruthy();
    expect(backend.savedIds(1)).toEqual(['sample-4']);
    expect(backend.savedIds(2)).toEqual([]);
  });

  it('does not ask for plans while nobody is signed in', async () => {
    render(<App />);
    await screen.findByRole('dialog', { hidden: true });
    expect(backend.callsTo('GET', '/api/plans')).toEqual([]);
  });

  it('the details view of an ended, unsaved event says it has ended', async () => {
    backend.plans.set(1, new Map([['past-1', '2026-11-01T09:00:00Z']]));
    render(<App />);
    await logIn('alex');
    goTo('My Plans');
    const past = (await within(myPlansPage()).findByRole('heading', { name: 'Past' })).closest('section');
    fireEvent.click(within(past).getByRole('button', { name: 'View details: Last week gallery night' }));
    const details = (await within(eventsPage()).findByRole('button', { name: 'Close details' })).closest('.panel');
    fireEvent.click(await within(details).findByRole('button', { name: 'Remove from My Plans: Last week gallery night' }));
    expect(await within(details).findByText('This event has ended.')).toBeTruthy();
    expect(within(details).queryByRole('button', { name: /Save to My Plans/ })).toBeNull();
  });
});

describe('Friends going in the whole app', () => {
  it("shows which friends are going, and opens a friend's plan from the Friends page", async () => {
    backend.follows = new Set(['1:2', '2:1', '3:1']); // Alex and Sam are friends; Pat follows Alex one way
    backend.plans.set(2, new Map([['sample-3', '2026-11-16T10:00:00Z']]));
    backend.plans.set(3, new Map([['sample-3', '2026-11-16T10:00:00Z']]));
    render(<App />);
    await logIn('alex');

    // The details view names Sam, not Pat.
    const card = (await within(eventsPage()).findByRole('heading', { name: 'North End food walk' })).closest('article');
    fireEvent.click(within(card).getByRole('button', { name: 'View details' }));
    const details = (await within(eventsPage()).findByRole('button', { name: 'Close details' })).closest('.panel');
    expect(await within(details).findByText('Sam is going')).toBeTruthy();

    // Friends page -> Sam's plans -> details on the Events page.
    goTo('Friends');
    const following = await screen.findByRole('region', { name: /^Following/ });
    expect(within(screen.getByRole('region', { name: /^Followers/ })).queryByRole('button', { name: 'See plans of @pat' })).toBeNull();
    fireEvent.click(within(following).getByRole('button', { name: 'See plans of @sam' }));
    const panel = await screen.findByRole('region', { name: "Sam's upcoming plans" });
    fireEvent.click(await within(panel).findByRole('button', { name: 'View details: North End food walk' }));
    await waitFor(() => expect(eventsPage().closest('[hidden]')).toBeNull());
    expect(screen.getByRole('button', { name: 'Events', current: 'page' })).toBeTruthy();
    expect(await within(eventsPage()).findByText('Sam is going')).toBeTruthy();
  });

  it('Sam sees Alex going once Alex saves the event', async () => {
    backend.follows = new Set(['1:2', '2:1']);
    render(<App />);
    await logIn('alex');
    const card = (await within(eventsPage()).findByRole('heading', { name: 'Harbor sunrise run' })).closest('article');
    fireEvent.click(within(card).getByRole('button', { name: /Save to My Plans/ }));
    await within(card).findByText('✓ In My Plans');
    await logOut();
    await logIn('sam');
    const samCard = (await within(eventsPage()).findByRole('heading', { name: 'Harbor sunrise run' })).closest('article');
    fireEvent.click(within(samCard).getByRole('button', { name: 'View details' }));
    expect(await within(eventsPage()).findByText('Alex is going')).toBeTruthy();
  });
});
