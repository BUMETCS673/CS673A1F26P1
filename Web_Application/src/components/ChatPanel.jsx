import React, { useState } from 'react';

const welcomeMessage = {
  sender: 'Assistant',
  text: 'Welcome! This is a placeholder for the Boston events chatbot. AI and catalog-based suggestions will be added here.',
};

export default function ChatPanel() {
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState([welcomeMessage]);

  function handleSubmit(event) {
    event.preventDefault();
    const request = draft.trim();
    if (!request) return;
    setMessages((previous) => [
      ...previous,
      { sender: 'You', text: request },
      {
        sender: 'Assistant',
        text: 'Sample reply: I cannot interpret requests yet. Try the category and date filters to explore the fictional event queue.',
      },
    ]);
    // Future feature: call the Python chat API here and render its reply.
    // Provider keys belong on the Python server, never in this component.
    setDraft('');
  }

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="section-heading">
        <h2 id="chat-title">Plan with a chat</h2>
        <span className="placeholder-badge">Placeholder</span>
      </div>
      <p className="muted-text">Preset replies only · AI is not connected</p>
      <div className="chat-messages" role="log" aria-label="Event conversation">
        {messages.map((message, index) => (
          <div className={`chat-message ${message.sender === 'You' ? 'from-user' : ''}`} key={index}>
            <strong>{message.sender}</strong>
            <p>{message.text}</p>
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <label htmlFor="chat-request">Ask about Boston events</label>
        <input
          id="chat-request"
          type="text"
          placeholder="For example: suggest music events this weekend"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <div className="buttons">
          <button className="primary-button" type="submit" disabled={!draft.trim()}>Send sample message</button>
          <button className="text-button" type="button" onClick={() => { setMessages([welcomeMessage]); setDraft(''); }}>Clear chat</button>
        </div>
      </form>
    </section>
  );
}
