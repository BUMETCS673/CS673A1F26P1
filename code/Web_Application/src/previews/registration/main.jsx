// AI-USAGE SUMMARY
// Authors: Junshuo Huang
// Tools: ChatGPT (reported by Junshuo Huang, weekly report week 6)
// Overall AI Contribution: ~95% for Junshuo Huang contributions
// AI-Assisted Areas: registration preview page
// Human Contributions: Junshuo Huang: form fields, validation rules, preview pages, shared styles (FV-114/115)
// Notes/Verification: checked in the preview pages and the Vite build (per weekly report)

import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import RegistrationForm from '../../components/RegistrationForm.jsx';

function RegistrationPreview() {
  const [submitted, setSubmitted] = useState(false);

  return (
    <main>
      <RegistrationForm onSubmit={() => setSubmitted(true)} />
      {submitted && (
        <p role="status" style={{ textAlign: 'center', fontFamily: 'system-ui, sans-serif' }}>
          Form submitted (preview)
        </p>
      )}
    </main>
  );
}

createRoot(document.getElementById('root')).render(<RegistrationPreview />);
