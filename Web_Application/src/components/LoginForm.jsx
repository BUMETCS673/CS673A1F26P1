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
