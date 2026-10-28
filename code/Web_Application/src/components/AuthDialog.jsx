// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: log in / register dialog
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
// Notes/Verification: manual browser testing on localhost:3000 (desktop and narrow widths); register, log in, reload, log out

import React, { useEffect, useRef, useState } from 'react';
import LoginForm from './LoginForm.jsx';
import RegistrationForm from './RegistrationForm.jsx';
import { logIn, register } from '../api.js';

// Blocks the website until the Python API accepts a username and password.
export default function AuthDialog({ onLogin }) {
  const dialogRef = useRef(null);
  const [mode, setMode] = useState('login');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [registered, setRegistered] = useState(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    // A native modal traps keyboard focus and blocks the page behind it.
    dialog.showModal();
    return () => dialog.close();
  }, []);

  function switchMode(nextMode) {
    setMode(nextMode);
    setError('');
    setRegistered(null);
  }

  async function handleLogin(credentials) {
    setPending(true);
    setError('');
    try {
      onLogin(await logIn(credentials));
    } catch (failure) {
      setError(failure.message);
      setPending(false);
    }
  }

  async function handleRegister(account) {
    setPending(true);
    setError('');
    try {
      const user = await register(account);
      // Send the new user to the login form so they sign in with what they chose.
      setRegistered(user.username);
      setMode('login');
    } catch (failure) {
      setError(failure.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="login-dialog"
      aria-label="Log in or create an account"
      onCancel={(event) => event.preventDefault()}
    >
      <p className="eyebrow">Boston Events</p>
      <div className="auth-switch" role="group" aria-label="Account type">
        <button type="button" aria-pressed={mode === 'login'} onClick={() => switchMode('login')}>
          Log in<span>Returning users</span>
        </button>
        <button type="button" aria-pressed={mode === 'register'} onClick={() => switchMode('register')}>
          Register<span>New users</span>
        </button>
      </div>
      {registered && (
        <p className="auth-notice" role="status">
          Account created for <strong>{registered}</strong>. Log in with your new password.
        </p>
      )}
      {/* The key resets each form's fields when switching between them. */}
      {mode === 'login' ? (
        <LoginForm
          key={`login-${registered ?? ''}`}
          onSubmit={handleLogin} error={error} pending={pending} defaultUsername={registered ?? ''}
        />
      ) : (
        <RegistrationForm key="register" onSubmit={handleRegister} error={error} pending={pending} />
      )}
    </dialog>
  );
}
