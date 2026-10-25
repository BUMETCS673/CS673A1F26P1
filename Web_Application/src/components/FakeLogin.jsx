import React, { useEffect, useRef } from 'react';

export default function FakeLogin({ onContinue }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    // A native modal traps keyboard focus and blocks the page behind it.
    dialog.showModal();
    return () => dialog.close();
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="login-dialog"
      aria-labelledby="login-title"
      aria-describedby="login-description"
      onCancel={(event) => event.preventDefault()}
    >
      <p className="eyebrow">Boston Events · Prototype</p>
      <span className="placeholder-badge">Explicitly fake login</span>
      <h1 id="login-title">Log in to explore Boston.</h1>
      <p id="login-description">The finished website will require an account before you can use it.</p>
      <div className="login-explanation">
        <strong>This pop-up is a placeholder.</strong>
        <p>
          Real registration, password checks, and login sessions must be added later.
          No account is created or checked here. This button only opens the demo.
        </p>
      </div>
      <button className="primary-button login-button" type="button" onClick={onContinue} autoFocus>
        Log In (fake for now, click to continue)
      </button>
      <p className="muted-text">Reloading the page or using the fake logout will show this pop-up again.</p>
    </dialog>
  );
}
