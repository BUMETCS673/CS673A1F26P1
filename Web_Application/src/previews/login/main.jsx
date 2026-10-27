// AI-USAGE SUMMARY
// Authors: Junshuo Huang
// Tools: ChatGPT (reported by Junshuo Huang, weekly report week 6)
// Overall AI Contribution: to be confirmed by Junshuo Huang
// AI-Assisted Areas: login preview page
// Human Contributions: Junshuo Huang: form fields, validation rules, preview pages, shared styles (FV-114/115)
// Notes/Verification: checked in the preview pages and the Vite build (per weekly report)

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
