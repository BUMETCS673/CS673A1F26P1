import React, { useId, useState } from 'react';
import './RegistrationForm.css';

const preferences = ['Music', 'Arts', 'Food', 'Outdoors', 'Social'];

// onSubmit receives { username, display_name, email, password, activity_preferences }.
export default function RegistrationForm({ onSubmit }) {
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
    <form className="registration-form" onSubmit={handleSubmit}>
      <h1>Registration form</h1>
      <p>All fields are required. Choose at least one activity preference.</p>

      <label htmlFor={`${id}-username`}>Username</label>
      <input id={`${id}-username`} name="username" autoComplete="username" maxLength={50} required />

      <label htmlFor={`${id}-display-name`}>Display name</label>
      <input id={`${id}-display-name`} name="display_name" autoComplete="nickname" maxLength={100} required />

      <label htmlFor={`${id}-email`}>Email</label>
      <input id={`${id}-email`} name="email" type="email" autoComplete="email" required />

      <label htmlFor={`${id}-password`}>Password</label>
      <input id={`${id}-password`} name="password" type="password" autoComplete="new-password" required />

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
      <button type="submit">Submit</button>
    </form>
  );
}
