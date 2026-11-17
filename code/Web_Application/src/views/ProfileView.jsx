// AI-USAGE SUMMARY
// Authors: Junshuo Huang (placeholder view), Daniel Winnie (FV-103 profile form, taking over from the Iteration 2 plan)
// Tools: OpenAI Codex, prompted by Junshuo Huang (placeholder); Claude Code (Claude Opus), prompted by Daniel Winnie (FV-103)
// Overall AI Contribution: 100% of the placeholder draft (Junshuo); ~90% of the FV-103 form (Daniel)
// AI-Assisted Areas: Profile placeholder view (Junshuo); editing display name and activity preferences through PATCH /api/auth/me (FV-103)
// Human Contributions: Junshuo Huang supplied the team navigation requirements; Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/views/ProfileView.test.jsx (npm test); browser check with two accounts

import React, { useId, useRef, useState } from 'react';
import { updateProfile } from '../api.js';
import './ProfileView.css';

// Same choices and order as registration (RegistrationForm.jsx).
const PREFERENCES = ['Music', 'Arts', 'Food', 'Outdoors', 'Social'];

/**
 * Props:
 *   user          the signed-in account from /api/auth/me
 *   onUserChange  called with the updated account after a successful save
 */
export default function ProfileView({ user, onUserChange }) {
  const id = useId();
  const [displayName, setDisplayName] = useState(user?.display_name ?? '');
  const [selected, setSelected] = useState(() => new Set(user?.activity_preferences ?? []));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const nameInput = useRef(null);
  const firstCheckbox = useRef(null);

  if (!user) return null;

  const chosen = PREFERENCES.filter((choice) => selected.has(choice));
  const unchanged = displayName.trim() === (user.display_name ?? '')
    && chosen.join() === PREFERENCES.filter((choice) => user.activity_preferences.includes(choice)).join();

  function toggle(choice) {
    setNotice('');
    setSelected((previous) => {
      const next = new Set(previous);
      if (next.has(choice)) next.delete(choice); else next.add(choice);
      return next;
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (saving) return;
    setError('');
    setNotice('');
    // The same rules as registration; the server checks them again.
    if (!displayName.trim()) {
      setError('Display name is required.');
      nameInput.current?.focus();
      return;
    }
    if (chosen.length === 0) {
      setError('Choose at least one activity preference.');
      firstCheckbox.current?.focus();
      return;
    }
    setSaving(true);
    try {
      const updated = await updateProfile({ display_name: displayName.trim(), activity_preferences: chosen });
      onUserChange?.(updated);
      setDisplayName(updated.display_name ?? '');
      setSelected(new Set(updated.activity_preferences));
      setNotice('Profile saved.');
    } catch (failure) {
      setError(failure.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="dashboard profile-view">
      <header className="page-heading">
        <p className="eyebrow">Profile</p>
        <h1>Your profile</h1>
        <p>Your display name is what friends see. Your activity preferences put those kinds of events
          first when you ask the chat without naming a category.</p>
      </header>

      <section className="panel" aria-labelledby={`${id}-account`}>
        <h2 id={`${id}-account`}>Account</h2>
        <dl className="profile-account">
          <dt>Username</dt><dd>@{user.username}</dd>
          <dt>Email</dt><dd>{user.email}</dd>
        </dl>
        <p className="muted-text">Your username and email can't be changed here.</p>
      </section>

      <form className="panel" onSubmit={handleSubmit} noValidate aria-labelledby={`${id}-edit`}>
        <h2 id={`${id}-edit`}>Edit profile</h2>
        <label htmlFor={`${id}-name`}>Display name</label>
        <input
          id={`${id}-name`}
          ref={nameInput}
          maxLength={100}
          value={displayName}
          autoComplete="nickname"
          aria-invalid={error === 'Display name is required.' || undefined}
          onChange={(event) => { setDisplayName(event.target.value); setNotice(''); }}
        />
        <fieldset className="profile-preferences">
          <legend>Activity preferences (choose at least one)</legend>
          {PREFERENCES.map((choice, index) => (
            <label key={choice} className="profile-choice">
              <input
                type="checkbox"
                ref={index === 0 ? firstCheckbox : undefined}
                checked={selected.has(choice)}
                onChange={() => toggle(choice)}
              />
              {choice}
            </label>
          ))}
        </fieldset>
        {error && <p className="profile-error" role="alert">{error}</p>}
        {notice && <p className="auth-notice" role="status">{notice}</p>}
        <div className="buttons">
          <button className="primary-button" type="submit" disabled={saving || unchanged}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </div>
      </form>
    </main>
  );
}
