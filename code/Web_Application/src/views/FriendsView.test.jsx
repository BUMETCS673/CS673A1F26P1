// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: Friends page tests: follow lists and friends' plans (mutual follows only), plus the details "friends going" line
// Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
// Notes/Verification: npm test

import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import FriendsView from './FriendsView.jsx';
import FriendsGoing from '../components/FriendsGoing.jsx';
import { createBackend, NOW } from '../testSupport/fakeBackend.js';

let backend;
beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] });
  vi.setSystemTime(NOW);
  backend = createBackend();
  backend.signedIn = 1; // Alex
  vi.stubGlobal('fetch', vi.fn(backend.fetch));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.useRealTimers(); });

const follow = (a, b) => backend.follows.add(`${a}:${b}`);
const save = (userId, ...ids) => ids.forEach((id) => backend.plans.set(userId,
  new Map([...(backend.plans.get(userId) ?? new Map()), [id, '2026-11-16T10:00:00Z']])));
const followingList = () => screen.getByRole('region', { name: /^Following/ });

describe('FriendsView: friends\' plans', () => {
  it('offers See plans only for mutual follows', async () => {
    follow(1, 2); follow(2, 1);   // Sam: mutual
    follow(1, 4);                 // Bea: Alex follows, not back
    follow(3, 1);                 // Pat: follows Alex, not back
    render(<FriendsView />);
    await screen.findByRole('heading', { name: 'Following (2)' });
    expect(screen.getAllByRole('button', { name: 'See plans of @sam' }).length).toBeGreaterThan(0);
    expect(screen.queryByRole('button', { name: 'See plans of @bea' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'See plans of @pat' })).toBeNull();
  });

  it("shows a friend's upcoming plans in start order, and each opens its details", async () => {
    follow(1, 2); follow(2, 1);
    save(2, 'sample-3', 'past-1', 'sample-1');
    const onEventSelect = vi.fn();
    render(<FriendsView onEventSelect={onEventSelect} />);
    fireEvent.click(within(await screen.findByRole('region', { name: /^Following/ }))
      .getByRole('button', { name: 'See plans of @sam' }));
    const panel = await screen.findByRole('region', { name: "Sam's upcoming plans" });
    await within(panel).findByText('Acoustic evening in Back Bay');
    const titles = within(panel).getAllByRole('listitem').map((item) => item.querySelector('strong').textContent);
    expect(titles).toEqual(['Acoustic evening in Back Bay', 'North End food walk']); // past-1 ended
    expect(within(panel).getByText('Sat, Nov 21 · 6:00 PM – 8:00 PM')).toBeTruthy();
    fireEvent.click(within(panel).getByRole('button', { name: 'View details: North End food walk' }));
    expect(onEventSelect).toHaveBeenCalledWith('sample-3');
    fireEvent.click(within(panel).getByRole('button', { name: 'Close' }));
    expect(screen.queryByRole('region', { name: "Sam's upcoming plans" })).toBeNull();
  });

  it('says so when a friend has no upcoming plans', async () => {
    follow(1, 3); follow(3, 1);
    render(<FriendsView />);
    fireEvent.click(within(await screen.findByRole('region', { name: /^Following/ }))
      .getByRole('button', { name: 'See plans of @pat' }));
    expect(await screen.findByText('@pat has no upcoming plans.')).toBeTruthy();
  });

  it('unfollowing the friend closes their plans', async () => {
    follow(1, 2); follow(2, 1);
    save(2, 'sample-1');
    render(<FriendsView />);
    fireEvent.click(within(await screen.findByRole('region', { name: /^Following/ }))
      .getByRole('button', { name: 'See plans of @sam' }));
    await screen.findByText('Acoustic evening in Back Bay');
    fireEvent.click(within(followingList()).getByRole('button', { name: 'Unfollow @sam' }));
    await waitFor(() => expect(screen.queryByRole('region', { name: "Sam's upcoming plans" })).toBeNull());
    expect(backend.follows.has('1:2')).toBe(false);
  });

  it('explains when the friend stopped following back in the meantime', async () => {
    follow(1, 2); follow(2, 1);
    render(<FriendsView />);
    const button = within(await screen.findByRole('region', { name: /^Following/ }))
      .getByRole('button', { name: 'See plans of @sam' });
    backend.follows.delete('2:1'); // Sam unfollows Alex in another browser
    fireEvent.click(button);
    expect((await screen.findByRole('alert')).textContent)
      .toBe("You can see Sam's plans only while you follow each other.");
  });

  it('switching friends shows the right plans', async () => {
    follow(1, 2); follow(2, 1); follow(1, 4); follow(4, 1);
    save(2, 'sample-1'); save(4, 'sample-3');
    render(<FriendsView />);
    const following = await screen.findByRole('region', { name: /^Following/ });
    fireEvent.click(within(following).getByRole('button', { name: 'See plans of @sam' }));
    await screen.findByText('Acoustic evening in Back Bay');
    fireEvent.click(within(following).getByRole('button', { name: 'See plans of @bea' }));
    const panel = await screen.findByRole('region', { name: "Bea's upcoming plans" });
    await within(panel).findByText('North End food walk');
    expect(within(panel).queryByText('Acoustic evening in Back Bay')).toBeNull();
  });
});

describe('FriendsGoing', () => {
  it('names mutual follows who saved the event', async () => {
    follow(1, 2); follow(2, 1); follow(1, 4); follow(4, 1); follow(3, 1);
    save(2, 'sample-1'); save(4, 'sample-1'); save(3, 'sample-1');
    render(<FriendsGoing eventId="sample-1" />);
    expect(await screen.findByText('Bea and Sam are going')).toBeTruthy();
  });

  it('shows nothing when no friend is going, or on an error', async () => {
    const { container } = render(<FriendsGoing eventId="sample-1" />);
    await waitFor(() => expect(backend.callsTo('GET', '/api/events/sample-1/friends-going')).toHaveLength(1));
    expect(container.innerHTML).toBe('');
    cleanup();
    backend.failNext('GET', '/api/events/sample-1/friends-going', 503);
    const second = render(<FriendsGoing eventId="sample-1" />);
    await waitFor(() => expect(backend.callsTo('GET', '/api/events/sample-1/friends-going')).toHaveLength(2));
    expect(second.container.innerHTML).toBe('');
  });

  it('updates when a different event is shown', async () => {
    follow(1, 2); follow(2, 1);
    save(2, 'sample-3');
    const { rerender } = render(<FriendsGoing eventId="sample-3" />);
    expect(await screen.findByText('Sam is going')).toBeTruthy();
    rerender(<FriendsGoing eventId="sample-1" />);
    await waitFor(() => expect(screen.queryByText('Sam is going')).toBeNull());
  });
});
