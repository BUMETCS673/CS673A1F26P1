// AI-USAGE SUMMARY
// Authors: Daniel Winnie (taking over "friends going" from the Iteration 2 plan)
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: "friends going" sentence
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/friendsGoing.test.js (npm test)

export const personName = (person) => person.display_name || `@${person.username}`;

// "Sam is going", "Sam and Bea are going", "3 friends are going: Bea, Pat, and Sam".
// Empty string when nobody is going.
export function friendsGoingText(friends) {
  const names = friends.map(personName);
  if (names.length === 0) return '';
  if (names.length === 1) return `${names[0]} is going`;
  if (names.length === 2) return `${names[0]} and ${names[1]} are going`;
  return `${names.length} friends are going: ${names.slice(0, -1).join(', ')}, and ${names.at(-1)}`;
}
