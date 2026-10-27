import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import LoginForm from '../../components/LoginForm.jsx';

function LoginPreview() {
  const [submitted, setSubmitted] = useState(false);
  const [showError, setShowError] = useState(false);

  return (
    <main>
      <LoginForm
        onSubmit={() => {
          setSubmitted(true);
          setShowError(false);
        }}
        error={showError ? 'Unable to sign in' : undefined}
      />
      <div style={{ textAlign: 'center', fontFamily: 'system-ui, sans-serif' }}>
        <button type="button" onClick={() => {
          setSubmitted(false);
          setShowError(value => !value);
        }}>
          Toggle example error
        </button>
        {submitted && <p role="status">Form submitted (preview)</p>}
      </div>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<LoginPreview />);
