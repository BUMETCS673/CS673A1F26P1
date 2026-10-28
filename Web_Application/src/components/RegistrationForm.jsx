// AI-USAGE SUMMARY
// Authors: Junshuo Huang, Daniel Winnie
// Tools: ChatGPT (reported by Junshuo Huang, weekly report week 6); Claude Code (Claude Opus), prompted by Daniel Winnie for later edits
// Overall AI Contribution: ~95% for Junshuo Huang contributions; later edits ~90%
// AI-Assisted Areas: registration form and validation (FV-114); later edit: connected to the auth API
// Human Contributions: Junshuo Huang: form fields, validation rules, preview pages, shared styles (FV-114/115)
// Notes/Verification: checked in the preview pages and the Vite build (per weekly report); later edits checked by the auth unit tests and manual login/registration in the browser

import React, { useId, useState } from 'react';
import './AuthForm.css';
import './RegistrationForm.css';

const preferences = ['Music', 'Arts', 'Food', 'Outdoors', 'Social'];

// onSubmit receives { username, display_name, email, password, activity_preferences }.
// error is an optional message; pending disables the button while a request runs.
export default function RegistrationForm({ onSubmit, error, pending = false }) {
  const id = useId();
  const [selected, setSelected] = useState([]);
  const [preferenceError, setPreferenceError] = useState(false);

  function togglePreference(choice) {
    const next = selected.includes(choice)
      ? selected.filter(value => value !== choice)
      : [...selected, choice];
    setSelected(next);
    if (next.length > 0) setPreferenceError(false);
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (selected.length === 0) {
      setPreferenceError(true);
      event.currentTarget.querySelector('input[type="checkbox"]').focus();
      return;
    }

    const values = new FormData(event.currentTarget);
    onSubmit({
      username: values.get('username'),
      display_name: values.get('display_name'),
      email: values.get('email'),
      password: values.get('password'),
      activity_preferences: [...selected],
    });
  }

  return (
    <form className="auth-form registration-form" onSubmit={handleSubmit}>
      <h1>Create an account</h1>
      <p>All fields are required. Choose at least one activity preference.</p>

      <label htmlFor={`${id}-username`}>Username</label>
      <input
        id={`${id}-username`} name="username" autoComplete="username" minLength={3} maxLength={50}
        pattern="[A-Za-z0-9_.\-]{3,50}" aria-describedby={`${id}-username-hint`} required autoFocus
      />
      <p id={`${id}-username-hint`} className="registration-form__hint">
        3–50 letters, numbers, periods, underscores, or hyphens.
      </p>

      <label htmlFor={`${id}-display-name`}>Display name</label>
      <input id={`${id}-display-name`} name="display_name" autoComplete="nickname" maxLength={100} required />

      <label htmlFor={`${id}-email`}>Email</label>
      <input id={`${id}-email`} name="email" type="email" autoComplete="email" maxLength={255} required />

      <label htmlFor={`${id}-password`}>Password</label>
      <input
        id={`${id}-password`} name="password" type="password" autoComplete="new-password"
        minLength={8} maxLength={128} aria-describedby={`${id}-password-hint`} required
      />
      <p id={`${id}-password-hint`} className="registration-form__hint">At least 8 characters.</p>

      <fieldset aria-describedby={preferenceError ? `${id}-preference-error` : undefined}>
        <legend>Activity preferences (choose at least one)</legend>
        <div className="registration-form__choices">
          {preferences.map(choice => (
            <label key={choice} className="registration-form__choice">
              <input
                type="checkbox"
                name="activity_preferences"
                value={choice}
                checked={selected.includes(choice)}
                onChange={() => togglePreference(choice)}
                aria-invalid={preferenceError || undefined}
                aria-describedby={preferenceError ? `${id}-preference-error` : undefined}
              />
              {choice}
            </label>
          ))}
        </div>
        {preferenceError && (
          <p id={`${id}-preference-error`} className="registration-form__error" role="alert">
            Select at least one activity preference.
          </p>
        )}
      </fieldset>
      {error && <p className="registration-form__error" role="alert">{error}</p>}
      <button type="submit" disabled={pending}>{pending ? 'Creating account…' : 'Create account'}</button>
    </form>
  );
}
