// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 chat integration tests (request sent, cards shown, card click, errors); FV-121 history load and clear
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: npm test

import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
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

// Replies by URL and method. `chat` is a list of replies used one per request.
let server;
function fakeServer({ history = [], chat = [], historyStatus = 200, clearStatus = 204 } = {}) {
  server = { history, chat: [...chat], historyStatus, clearStatus };
}
function chatCalls() {
  return fetch.mock.calls.filter(([url]) => url === '/api/chat');
}

beforeEach(() => {
  fakeServer();
  vi.stubGlobal('fetch', vi.fn((url, options = {}) => {
    if (url === '/api/chat/history' && options.method === 'DELETE') {
      return server.clearStatus === 204
        ? Promise.resolve(new Response(null, { status: 204 }))
        : jsonResponse({ detail: 'Chat history could not be cleared. Please try again.' }, server.clearStatus);
    }
    if (url === '/api/chat/history') {
      return jsonResponse(server.historyStatus === 200 ? { messages: server.history } : {}, server.historyStatus);
    }
    const [body, status] = server.chat.shift();
    return jsonResponse(body, status);
  }));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe('ChatPanel', () => {
  it('sends the request text to POST /api/chat and shows the matching cards', async () => {
    fakeServer({ chat: [[REPLY, 200]] });
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('  music  ');

    expect(await screen.findByRole('button', { name: /Acoustic evening in Back Bay/ })).toBeTruthy();
    const [url, options] = chatCalls()[0];
    expect(url).toBe('/api/chat');
    expect(options.method).toBe('POST');
    expect(JSON.parse(options.body)).toEqual({ message: 'music' });
    expect(screen.getByText('music').closest('.from-user')).toBeTruthy();
  });

  it('reports the event ID when a card is clicked', async () => {
    fakeServer({ chat: [[REPLY, 200]] });
    const onEventSelect = vi.fn();
    render(<ChatPanel onEventSelect={onEventSelect} />);
    ask('music');
    fireEvent.click(await screen.findByRole('button', { name: /Acoustic evening/ }));
    expect(onEventSelect).toHaveBeenCalledWith('sample-1');
  });

  it('shows the clarification view for a request it did not understand', async () => {
    fakeServer({ chat: [[{
      interpretation: { ...REPLY.interpretation, category: null, needs_clarification: true },
      events: [],
    }, 200]] });
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('asdf');
    expect(await screen.findByText('Could you rephrase that?')).toBeTruthy();
  });

  it('shows the server error message when the request fails', async () => {
    fakeServer({ chat: [[{ detail: 'Chat history is unavailable right now, so this message was not saved. Please try again.' }, 503]] });
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('music');
    expect((await screen.findByRole('alert')).textContent).toContain('was not saved');
    expect(screen.queryByRole('button', { name: /Acoustic evening/ })).toBeNull();
  });

  it('shows saved history on open, with cards rebuilt by the server', async () => {
    fakeServer({ history: [{
      id: 1, request_text: 'music', created_at: '2026-11-14T20:00:00Z',
      interpretation: REPLY.interpretation, events: REPLY.events, unavailable_count: 2,
    }] });
    render(<ChatPanel onEventSelect={() => {}} />);
    expect(await screen.findByRole('button', { name: /Acoustic evening/ })).toBeTruthy();
    expect(screen.getByText('music').closest('.from-user')).toBeTruthy();
    expect(screen.getByText('2 earlier results have ended or are no longer available.')).toBeTruthy();
  });

  it('still works when history cannot be loaded', async () => {
    fakeServer({ historyStatus: 503, chat: [[REPLY, 200]] });
    render(<ChatPanel onEventSelect={() => {}} />);
    expect((await screen.findByRole('alert')).textContent).toContain("couldn't be loaded");
    ask('music');
    expect(await screen.findByRole('button', { name: /Acoustic evening/ })).toBeTruthy();
  });

  it('Clear history deletes on the server and empties the chat', async () => {
    fakeServer({ chat: [[REPLY, 200]] });
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('music');
    await screen.findByRole('button', { name: /Acoustic evening/ });
    fireEvent.click(screen.getByRole('button', { name: 'Clear history' }));
    await waitFor(() => expect(screen.queryByRole('button', { name: /Acoustic evening/ })).toBeNull());
    expect(fetch.mock.calls.some(([url, options]) => url === '/api/chat/history'
      && options?.method === 'DELETE')).toBe(true);
  });

  it('keeps the messages and says so when clearing fails', async () => {
    fakeServer({ chat: [[REPLY, 200]], clearStatus: 503 });
    render(<ChatPanel onEventSelect={() => {}} />);
    ask('music');
    await screen.findByRole('button', { name: /Acoustic evening/ });
    fireEvent.click(screen.getByRole('button', { name: 'Clear history' }));
    expect((await screen.findByRole('alert')).textContent).toContain('History was not cleared');
    expect(screen.getByRole('button', { name: /Acoustic evening/ })).toBeTruthy();
  });
});
