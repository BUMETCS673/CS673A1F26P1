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
