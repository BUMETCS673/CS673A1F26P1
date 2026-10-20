// React lets us describe the page with JSX (HTML-like code in JavaScript).
import React from 'react';
// createRoot connects React to an element in our index.html file.
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

// Render means "display on the page." App is our main component.
createRoot(document.getElementById('root')).render(<App />);
