// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 fictional mock chat responses for the standalone preview
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/components/RecommendationResults.test.jsx; standalone preview

// Fictional events in the FV-122/FV-123 catalog shape. Not real listings.
const events = {
  jazz: {
    id: 'mock-101',
    title: 'Mock: Late jazz set in Cambridge',
    category: 'Music',
    start: '2026-11-13T19:30:00-05:00',
    end: '2026-11-13T22:00:00-05:00',
    location: 'Central Square, Cambridge',
    description: 'Fictional preview event.',
  },
  choir: {
    id: 'mock-102',
    title: 'Mock: Community choir showcase',
    category: 'Music',
    start: '2026-11-13T18:30:00-05:00',
    end: '2026-11-13T20:00:00-05:00',
    location: 'Back Bay, Boston',
    description: 'Fictional preview event.',
  },
  dj: {
    id: 'mock-103',
    title: 'Mock: Harbor DJ night (ends after midnight)',
    category: 'Music',
    start: '2026-11-13T21:00:00-05:00',
    end: '2026-11-14T01:00:00-05:00',
    location: 'Seaport, Boston',
    description: 'Fictional preview event.',
  },
  pasta: {
    id: 'mock-201',
    title: 'Mock: Fresh pasta workshop',
    category: 'Food',
    start: '2026-11-15T12:00:00-05:00',
    end: '2026-11-15T14:00:00-05:00',
    location: 'North End, Boston',
    description: 'Fictional preview event.',
  },
  trivia: {
    id: 'mock-301',
    title: 'Mock: Neighborhood trivia night',
    category: 'Social',
    start: '2026-11-11T19:00:00-05:00',
    end: '2026-11-11T21:00:00-05:00',
    location: 'Jamaica Plain, Boston',
    description: 'Fictional preview event.',
  },
};

// Parser output shape from FV-124 (app/request_parser.py).
function interpretation(fields) {
  return {
    category: null, date: null, time: null, time_operator: null,
    location: null, location_operator: null, timezone: 'America/New_York',
    needs_clarification: false, ...fields,
  };
}

export const CLARIFICATION = {
  interpretation: { ...interpretation({}), timezone: null, needs_clarification: true },
  events: [],
};

// Canned replies keyed by lowercase request text. The preview reference date is
// Tuesday, Nov 10, 2026 in Boston, so "this friday" is 2026-11-13.
export const MOCK_REPLIES = {
  'music this friday after 6pm': {
    interpretation: interpretation({ category: 'Music', date: '2026-11-13', time: '18:00', time_operator: 'after' }),
    events: [events.choir, events.jazz, events.dj],
  },
  'food near north end': {
    interpretation: interpretation({ category: 'Food', location: 'North End', location_operator: 'near' }),
    events: [events.pasta],
  },
  'something fun tomorrow': {
    interpretation: interpretation({ date: '2026-11-11' }),
    events: [events.trivia],
  },
  'outdoors in allston at 7am': {
    interpretation: interpretation({
      category: 'Outdoors', time: '07:00', time_operator: 'at', location: 'Allston', location_operator: 'in',
    }),
    events: [],
  },
};

// Anything not listed above is treated like text the parser could not read.
export function mockChatReply(text) {
  return MOCK_REPLIES[text.trim().toLowerCase().replace(/\s+/g, ' ')] ?? CLARIFICATION;
}
