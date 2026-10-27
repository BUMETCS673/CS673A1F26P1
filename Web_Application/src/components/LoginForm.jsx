import React, { useId } from 'react';
import './AuthForm.css';
import './LoginForm.css';

// onSubmit receives { username, password }. error is an optional message.
export default function LoginForm({ onSubmit, error }) {
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
      <input id={`${id}-username`} name="username" autoComplete="username" required />
      <label htmlFor={`${id}-password`}>Password</label>
      <input id={`${id}-password`} name="password" type="password" autoComplete="current-password" required />
      {error && <p id={`${id}-error`} className="login-form__error" role="alert">{error}</p>}
      <button type="submit">Log In</button>
    </form>
  );
}
