// AI-USAGE SUMMARY
// Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: shared Save to My Plans button (FV-95)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/components/SaveButton.test.jsx (npm test)

import React, { useState } from 'react';
import { usePlans } from '../plans.jsx';
import './SaveButton.css';

/**
 * "Save to My Plans" for one event, or "In My Plans" with a Remove button once saved.
 *
 * Props:
 *   eventId     the catalog event ID
 *   eventTitle  used in the button's accessible name, so screen readers know which event
 *   ended       optional; true hides the Save button (ended events cannot be saved)
 *
 * Renders nothing outside a PlansProvider.
 */
export default function SaveButton({ eventId, eventTitle, ended = false }) {
  const plans = usePlans();
  const [error, setError] = useState('');
  if (!plans) return null;

  const saved = plans.savedIds.has(eventId);
  const pending = plans.pendingIds.has(eventId);
  const name = eventTitle ? `: ${eventTitle}` : '';

  async function run(action) {
    setError('');
    try {
      await action(eventId);
    } catch (failure) {
      setError(failure.message);
    }
  }

  let control;
  if (saved) {
    control = (
      <>
        <span className="plan-saved">✓ In My Plans</span>
        <button
          className="secondary-button"
          type="button"
          disabled={pending}
          aria-label={`Remove from My Plans${name}`}
          onClick={() => run(plans.remove)}
        >
          {pending ? 'Removing…' : 'Remove from My Plans'}
        </button>
      </>
    );
  } else if (ended) {
    control = <span className="muted-text">This event has ended.</span>;
  } else {
    control = (
      <button
        className="primary-button"
        type="button"
        disabled={pending}
        aria-label={`Save to My Plans${name}`}
        onClick={() => run(plans.save)}
      >
        {pending ? 'Saving…' : 'Save to My Plans'}
      </button>
    );
  }

  return (
    <div className="save-plan">
      {control}
      {error && <p className="save-plan-error" role="alert">{error}</p>}
    </div>
  );
}
