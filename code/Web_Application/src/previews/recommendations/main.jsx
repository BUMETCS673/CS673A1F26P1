// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: FV-125 standalone recommendation results preview
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: opened /src/previews/recommendations/ in Vite (desktop and narrow widths)

// Standalone preview: no backend, no login. Replies come from mockResponses.js,
// and clicking a card only records its ID (placeholder for the details view).

import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import RecommendationResults from '../../components/RecommendationResults.jsx';
import { MOCK_REPLIES, mockChatReply } from './mockResponses.js';
import '../../styles.css';

function RecommendationsPreview() {
  const [draft, setDraft] = useState('');
  const [turns, setTurns] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  function ask(text) {
    const request = text.trim();
    if (!request) return;
    setTurns((previous) => [...previous, { request, response: mockChatReply(request) }]);
    setDraft('');
  }

  return (
    <main className="dashboard" style={{ maxWidth: 560 }}>
      <p className="eyebrow">FV-125 preview</p>
      <h1>Recommendation results</h1>
      <p className="prototype-note" style={{ marginTop: 12 }}>
        Mock replies only. Try one of: {Object.keys(MOCK_REPLIES).map((key) => `"${key}"`).join(', ')}.
        Anything else shows the clarification view.
      </p>

      <section className="panel" style={{ marginTop: 16 }} aria-label="Preview chat">
        {turns.length === 0 && <p className="muted-text">Send a request to see results.</p>}
        {turns.map((turn, index) => (
          <div className="chat-message" key={index} style={{ marginBottom: 16 }}>
            <p><strong>You:</strong> {turn.request}</p>
            <RecommendationResults response={turn.response} onEventSelect={setSelectedId} onSuggestion={ask} />
          </div>
        ))}
        <form onSubmit={(event) => { event.preventDefault(); ask(draft); }} style={{ display: 'grid', gap: 8 }}>
          <label htmlFor="preview-request">Request text</label>
          <input id="preview-request" value={draft} maxLength={1000} onChange={(event) => setDraft(event.target.value)}
            placeholder="music this friday after 6pm" />
          <div className="buttons">
            <button className="primary-button" type="submit" disabled={!draft.trim()}>Send</button>
            <button className="text-button" type="button" onClick={() => { setTurns([]); setSelectedId(null); }}>Clear</button>
          </div>
        </form>
      </section>

      <p role="status" style={{ marginTop: 12 }}>
        {selectedId ? `Card clicked: would open event details for ${selectedId}` : 'No card clicked yet.'}
      </p>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<RecommendationsPreview />);
