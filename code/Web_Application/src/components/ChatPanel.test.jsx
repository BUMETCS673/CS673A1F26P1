// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 chat integration tests (request sent, cards shown, card click, errors)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: npm test

import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import ChatPanel from './ChatPanel.jsx';

const REPLY = {
  interpretation: {
    category: 'Music', date: null, time: null, time_operator: null,
    location: null, location_operator: null, timezone: 'America/New_York',
    needs_clarification: false,
  },
  events: [{
    id: 'sample-1', title: 'Acoustic evening in Back Bay', category: 'Music',
    start: '2026-11-21T18:00:00-05:00', end: '2026-11-21T20:00:00-05:00',
    location: 'Back Bay, Boston', description: 'Fictional.',
  }],
};

function jsonResponse(body, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), {
    status, headers: { 'Content-Type': 'application/json' },
  }));
}

function ask(text) {
  fireEvent.change(screen.getByLabelText('Your request'), { target: { value: text } });
  fireEvent.click(screen.getByRole('button', { name: 'Send' }));
}

beforeEach(() => { vi.stubGlobal('fetch', vi.fn()); });
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe('ChatPanel', () => {
  it('sends the request text to POST /api/chat and shows the matching cards', async () => {
    fetch.mockReturnValueOnce(jsonResponse(REPLY));
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('  music  ');

    expect(await screen.findByRole('button', { name: /Acoustic evening in Back Bay/ })).toBeTruthy();
    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/chat');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ message: 'music' });
    expect(screen.getByText('music').closest('.from-user')).toBeTruthy();
  });

  it('reports the event ID when a card is clicked', async () => {
    fetch.mockReturnValueOnce(jsonResponse(REPLY));
    const onEventSelect = vi.fn();
    render(<ChatPanel onEventSelect={onEventSelect} />);
    ask('music');
    fireEvent.click(await screen.findByRole('button', { name: /Acoustic evening/ }));
    expect(onEventSelect).toHaveBeenCalledWith('sample-1');
  });

  it('shows the clarification view for a request it did not understand', async () => {
    fetch.mockReturnValueOnce(jsonResponse({
      interpretation: { ...REPLY.interpretation, category: null, needs_clarification: true },
      events: [],
    }));
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('asdf');
    expect(await screen.findByText('Could you rephrase that?')).toBeTruthy();
  });

  it('shows the server error message when the request fails', async () => {
    fetch.mockReturnValueOnce(jsonResponse({ detail: 'Not logged in.' }, 401));
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('music');
    expect((await screen.findByRole('alert')).textContent).toBe('Not logged in.');
  });

  it('Clear chat removes earlier messages', async () => {
    fetch.mockReturnValueOnce(jsonResponse(REPLY));
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('music');
    await screen.findByRole('button', { name: /Acoustic evening/ });
    fireEvent.click(screen.getByRole('button', { name: 'Clear chat' }));
    expect(screen.queryByRole('button', { name: /Acoustic evening/ })).toBeNull();
  });
});
