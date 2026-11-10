// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 component tests for event cards, clarification, and no matches
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: npm test

import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import RecommendationResults, { EXAMPLE_REQUESTS } from './RecommendationResults.jsx';
import { CLARIFICATION, MOCK_REPLIES, mockChatReply } from '../previews/recommendations/mockResponses.js';

afterEach(cleanup);

const friday = MOCK_REPLIES['music this friday after 6pm'];
const noMatches = MOCK_REPLIES['outdoors in allston at 7am'];

describe('RecommendationResults: event cards', () => {
  it('renders one card per event in the order received', () => {
    render(<RecommendationResults response={friday} onEventSelect={() => {}} />);
    const cards = screen.getAllByRole('button', { name: /View event details/ });
    expect(cards.map((card) => card.getAttribute('aria-label'))).toEqual(
      friday.events.map((event) => `${event.title}. View event details`),
    );
    expect((screen.getByRole('status')).textContent).toContain('3 events match');
  });

  it('shows category, Boston time, and location on a card', () => {
    render(<RecommendationResults response={friday} onEventSelect={() => {}} />);
    const card = screen.getByRole('button', { name: /Late jazz set/ });
    expect((card).textContent).toContain('Music');
    expect((card).textContent).toContain('Fri, Nov 13 · 7:30 PM – 10:00 PM');
    expect((card).textContent).toContain('Central Square, Cambridge');
    expect(card.querySelector('time').getAttribute('datetime')).toBe('2026-11-13');
  });

  it('shows the understood conditions above the cards', () => {
    render(<RecommendationResults response={friday} onEventSelect={() => {}} />);
    const conditions = screen.getByRole('list', { name: 'Understood conditions' });
    expect(within(conditions).getAllByRole('listitem').map((item) => item.textContent))
      .toEqual(['Music', 'Fri, Nov 13', 'after 6:00 PM']);
  });

  it('uses the singular for one event', () => {
    render(<RecommendationResults response={MOCK_REPLIES['food near north end']} />);
    expect((screen.getByRole('status')).textContent).toContain('1 event match');
  });

  it('passes only the event ID to the click callback', () => {
    const onEventSelect = vi.fn();
    render(<RecommendationResults response={friday} onEventSelect={onEventSelect} />);
    fireEvent.click(screen.getByRole('button', { name: /Harbor DJ night/ }));
    expect(onEventSelect).toHaveBeenCalledTimes(1);
    expect(onEventSelect).toHaveBeenCalledWith('mock-103');
  });

  it('does not crash when no click callback is given', () => {
    render(<RecommendationResults response={friday} />);
    fireEvent.click(screen.getByRole('button', { name: /Late jazz set/ }));
  });

  it('handles a card with missing optional fields', () => {
    render(<RecommendationResults response={{
      interpretation: { needs_clarification: false },
      events: [{ id: 'bare', title: 'Bare event', start: null }],
    }} />);
    const card = screen.getByRole('button', { name: /Bare event/ });
    expect((card).textContent).toContain('Time to be announced');
    expect(card.querySelector('time').hasAttribute('datetime')).toBe(false);
  });
});

describe('RecommendationResults: clarification', () => {
  it('asks the user to rephrase and lists no events', () => {
    render(<RecommendationResults response={CLARIFICATION} onEventSelect={() => {}} />);
    expect(screen.getByRole('heading', { name: 'Could you rephrase that?' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /View event details/ })).toBeNull();
    expect(screen.queryByRole('list', { name: 'Understood conditions' })).toBeNull();
  });

  it('shows a server-provided message when there is one', () => {
    render(<RecommendationResults response={{ ...CLARIFICATION, message: 'Which day did you mean?' }} />);
    expect(screen.getByText('Which day did you mean?')).toBeTruthy();
  });

  it('sends an example request when a suggestion is clicked', () => {
    const onSuggestion = vi.fn();
    render(<RecommendationResults response={CLARIFICATION} onSuggestion={onSuggestion} />);
    fireEvent.click(screen.getByRole('button', { name: EXAMPLE_REQUESTS[1] }));
    expect(onSuggestion).toHaveBeenCalledWith(EXAMPLE_REQUESTS[1]);
  });

  it('hides suggestions when no handler is given', () => {
    render(<RecommendationResults response={CLARIFICATION} />);
    expect(screen.queryByRole('button')).toBeNull();
  });
});

describe('RecommendationResults: no matches', () => {
  it('explains that nothing matched and repeats the conditions', () => {
    render(<RecommendationResults response={noMatches} onSuggestion={() => {}} />);
    expect(screen.getByRole('heading', { name: 'No matching events' })).toBeTruthy();
    const conditions = screen.getByRole('list', { name: 'Understood conditions' });
    expect(within(conditions).getAllByRole('listitem').map((item) => item.textContent))
      .toEqual(['Outdoors', 'at 7:00 AM', 'in Allston']);
    expect(screen.queryByRole('button', { name: /View event details/ })).toBeNull();
    expect(screen.getAllByRole('button')).toHaveLength(EXAMPLE_REQUESTS.length);
  });
});

describe('mock chat replies', () => {
  it('normalizes case and spacing', () => {
    expect(mockChatReply('  Food   NEAR north end ')).toBe(MOCK_REPLIES['food near north end']);
  });

  it('falls back to clarification for unknown text', () => {
    expect(mockChatReply('surprise me')).toBe(CLARIFICATION);
  });

  it('every example suggestion has a canned reply with results', () => {
    for (const example of EXAMPLE_REQUESTS) {
      expect(mockChatReply(example).events.length).toBeGreaterThan(0);
    }
  });

  it('mock events have unique IDs and catalog-shaped times', () => {
    const all = Object.values(MOCK_REPLIES).flatMap((reply) => reply.events);
    const ids = new Set(all.map((event) => event.id));
    expect(ids.size).toBe(new Set(all).size);
    for (const event of all) {
      expect(event.start).toMatch(/[+-]\d{2}:\d{2}$/);
      expect(event.end).toMatch(/[+-]\d{2}:\d{2}$/);
    }
  });
});
