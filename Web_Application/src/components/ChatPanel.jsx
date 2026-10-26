import React, { useEffect, useRef, useState } from 'react';

const welcomeMessage = {
  sender: 'Assistant',
  text: "Test the Python parser with 'music' or 'Music on 2026-11-01'. Supported categories: Music, Arts, Food, Outdoors, Social. The response shows category, date, and needs_clarification. This branch only parses requests; it does not search events.",
};

export default function ChatPanel() {
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState([welcomeMessage]);
  const [isSending, setIsSending] = useState(false);
  const pendingRequest = useRef(null);
  const conversation = useRef(null);

  useEffect(() => () => pendingRequest.current?.abort(), []);
  useEffect(() => {
    if (conversation.current) {
      conversation.current.scrollTop = conversation.current.scrollHeight;
    }
  }, [messages, isSending]);

  async function handleSubmit(event) {
    event.preventDefault();
    const request = draft.trim();
    if (!request || pendingRequest.current) return;
    const controller = new AbortController();
    pendingRequest.current = controller;
    const timeout = setTimeout(() => controller.abort('timeout'), 15000);
    setMessages((previous) => [...previous, { sender: 'You', text: request }]);
    setDraft('');
    setIsSending(true);
    try {
      // This demo only calls FV-118; it sends no event catalog or filter request.
      const response = await fetch('/api/demo/parse-event-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: request }),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error('Demo request failed');
      const result = await response.json();
      if (controller.signal.aborted) return;
      setMessages((previous) => [...previous, {
        sender: 'Assistant',
        text: result.needs_clarification
          ? "Please clarify: use Music, Arts, Food, Outdoors, or Social, optionally followed by 'on YYYY-MM-DD' with a valid date. Relative dates and other phrases are not supported."
          : 'Request recognized. Parsed conditions:',
        interpretation: result,
      }]);
    } catch {
      // Clear chat/logout cancels silently; a timeout or service failure is shown.
      if (controller.signal.aborted && controller.signal.reason !== 'timeout') return;
      setMessages((previous) => [...previous, {
        sender: 'Assistant', error: true,
        text: 'Could not reach the demo service. Check that the Python backend is running, then try your request again.',
      }]);
    } finally {
      clearTimeout(timeout);
      if (pendingRequest.current === controller) {
        pendingRequest.current = null;
        setIsSending(false);
      }
    }
  }

  function clearChat() {
    pendingRequest.current?.abort();
    pendingRequest.current = null;
    setIsSending(false);
    setMessages([welcomeMessage]);
    setDraft('');
  }

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="section-heading">
        <h2 id="chat-title">Plan with a chat</h2>
        <span className="placeholder-badge">Parser demo</span>
      </div>
      <p className="muted-text">Python request parsing · no event search · no AI key</p>
      <div className="chat-messages" role="log" aria-label="Event conversation" ref={conversation}>
        {messages.map((message, index) => (
          <div className={`chat-message ${message.sender === 'You' ? 'from-user' : ''}`} key={index}>
            <strong>{message.sender}</strong>
            <p role={message.error ? 'alert' : undefined}>{message.text}</p>
            {message.interpretation && (
              <pre className="parsed-request" aria-label="Parsed request">
                {JSON.stringify(message.interpretation, null, 2)}
              </pre>
            )}
          </div>
        ))}
        {isSending && <p role="status">Parsing request…</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <label htmlFor="chat-request">Request text</label>
        <input
          id="chat-request"
          type="text"
          placeholder="Music on 2026-11-01"
          maxLength={1000}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <div className="buttons">
          <button className="primary-button" type="submit" disabled={!draft.trim() || isSending}>
            {isSending ? 'Parsing…' : 'Parse request'}
          </button>
          <button className="text-button" type="button" onClick={clearChat}>Clear chat</button>
        </div>
      </form>
    </section>
  );
}
