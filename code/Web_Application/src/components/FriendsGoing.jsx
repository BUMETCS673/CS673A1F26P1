// AI-USAGE SUMMARY
// Authors: Daniel Winnie (taking over "friends going" from the Iteration 2 plan)
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: "friends going" line in the event details view
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/components/FriendsGoing.test.jsx (npm test); browser check with three accounts

import React, { useEffect, useState } from 'react';
import { getFriendsGoing } from '../api.js';
import { friendsGoingText } from '../friendsGoing.js';

/**
 * "Sam is going" for one event: mutual follows who saved it. Shows nothing when
 * nobody is going or the answer can't be loaded (it is extra information, so a
 * failure should not get in the way of the details).
 */
export default function FriendsGoing({ eventId }) {
  const [friends, setFriends] = useState([]);

  useEffect(() => {
    let current = true;
    setFriends([]);
    getFriendsGoing(eventId)
      .then((data) => { if (current) setFriends(data.friends); })
      .catch(() => {});
    return () => { current = false; };
  }, [eventId]);

  const text = friendsGoingText(friends);
  if (!text) return null;
  return <p className="friends-going">{text}</p>;
}
