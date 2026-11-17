// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: "friends going" sentence tests
// Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
// Notes/Verification: npm test

import { describe, expect, it } from 'vitest';
import { friendsGoingText, personName } from './friendsGoing.js';

const sam = { id: 2, username: 'sam', display_name: 'Sam' };
const bea = { id: 4, username: 'bea', display_name: 'Bea' };
const pat = { id: 3, username: 'pat', display_name: null };

describe('friendsGoingText', () => {
  it('is empty when nobody is going', () => expect(friendsGoingText([])).toBe(''));
  it('names one friend', () => expect(friendsGoingText([sam])).toBe('Sam is going'));
  it('names two friends', () => expect(friendsGoingText([bea, sam])).toBe('Bea and Sam are going'));
  it('counts and lists three or more', () => {
    expect(friendsGoingText([bea, pat, sam])).toBe('3 friends are going: Bea, @pat, and Sam');
  });
  it('uses the username when there is no display name', () => expect(personName(pat)).toBe('@pat'));
});
