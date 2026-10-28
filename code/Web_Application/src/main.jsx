// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: React entry point and beginner comments
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
// Notes/Verification: manual browser testing on localhost:3000 (desktop and narrow widths)

// React lets us describe the page with JSX (HTML-like code in JavaScript).
import React from 'react';
// createRoot connects React to an element in our index.html file.
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';

// Render means "display on the page." App is our main component.
createRoot(document.getElementById('root')).render(<App />);
