// AI-USAGE SUMMARY
// Authors: Junshuo Huang, Daniel Winnie
// Tools: ChatGPT (reported by Junshuo Huang, weekly report week 6); Claude Code (Claude Opus), prompted by Daniel Winnie for later edits
// Overall AI Contribution: to be confirmed by Junshuo Huang; later edits ~90%
// AI-Assisted Areas: login form and error display (FV-115); later edit: connected to the auth API
// Human Contributions: Junshuo Huang: form fields, validation rules, preview pages, shared styles (FV-114/115)
// Notes/Verification: checked in the preview pages and the Vite build (per weekly report); later edits checked by the auth unit tests and manual login/registration in the browser

import React, { useId } from 'react';
import './AuthForm.css';
import './LoginForm.css';

// onSubmit receives { username, password }. error is an optional message.
// pending disables the button while a request runs; defaultUsername pre-fills it.
export default function LoginForm({ onSubmit, error, pending = false, defaultUsername = '' }) {
  const id = useId();

  function handleSubmit(event) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    onSubmit({
      username: values.get('username'),
      password: values.get('password'),
    });
  }

  return (
    <form className="auth-form login-form" onSubmit={handleSubmit} aria-describedby={error ? `${id}-error` : undefined}>
      <h1>Log in</h1>
      <p>Both fields are required.</p>
      <label htmlFor={`${id}-username`}>Username</label>
      <input
        id={`${id}-username`} name="username" autoComplete="username" maxLength={50} required
        defaultValue={defaultUsername} autoFocus={!defaultUsername}
      />
      <label htmlFor={`${id}-password`}>Password</label>
      <input
        id={`${id}-password`} name="password" type="password" autoComplete="current-password"
        maxLength={128} required autoFocus={Boolean(defaultUsername)}
      />
      {error && <p id={`${id}-error`} className="login-form__error" role="alert">{error}</p>}
      <button type="submit" disabled={pending}>{pending ? 'Logging in…' : 'Log In'}</button>
    </form>
  );
}
