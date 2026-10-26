import React, { useEffect, useRef, useState } from 'react';

const welcomeMessage = {
  sender: 'Assistant',
  text: 'Test the Python filter with JSON conditions. For example: {"category":"Music","date":"2026-11-01"}. Use {"category":"Music"} for any date, {"date":"2026-11-01"} for any category, or {} for all samples. This demo does not parse natural-language requests.',
};

export default function ChatPanel({ events }) {
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
    let filters;
    try {
      filters = JSON.parse(request);
      if (!filters || Array.isArray(filters) || typeof filters !== 'object'
          || Object.keys(filters).some((key) => !['category', 'date'].includes(key))
          || Object.values(filters).some((value) => value !== null && typeof value !== 'string')) {
        throw new Error('Invalid filter conditions');
      }
    } catch {
      setMessages((previous) => [...previous, { sender: 'You', text: request }, {
        sender: 'Assistant', error: true,
        text: 'Enter a JSON object with only category and/or date, for example {"category":"Music","date":"2026-11-01"}. This branch tests filtering, not natural-language parsing.',
      }]);
      return;
    }
    const controller = new AbortController();
    pendingRequest.current = controller;
    const timeout = setTimeout(() => controller.abort('timeout'), 15000);
    setMessages((previous) => [...previous, { sender: 'You', text: request }]);
    setDraft('');
    setIsSending(true);
    try {
      // Send the full existing sample list, independent of the sidebar filters.
      // This is deliberately a demo adapter, not an authoritative event catalog.
      const response = await fetch('/api/demo/filter-events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...filters, events }),
        signal: controller.signal,
      });
      if (response.status === 422) {
        throw new Error('Use category up to 50 characters and date up to 10 characters.');
      }
      if (!response.ok) throw new Error('Demo request failed');
      const result = await response.json();
      if (controller.signal.aborted) return;
      setMessages((previous) => [...previous, {
        sender: 'Assistant', text: result.message,
        filters: { category: result.category, date: result.date }, events: result.events,
      }]);
    } catch (error) {
      // Clear chat/logout cancels silently; a timeout or service failure is shown.
      if (controller.signal.aborted && controller.signal.reason !== 'timeout') return;
      setMessages((previous) => [...previous, {
        sender: 'Assistant', error: true,
        text: error.message.startsWith('Use category') ? error.message
          : 'Could not reach the demo service. Check that the Python backend is running, then try your request again.',
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
        <span className="placeholder-badge">Filter demo</span>
      </div>
      <p className="muted-text">Explicit JSON filters · Python backend · sample data only</p>
      <div className="chat-messages" role="log" aria-label="Event conversation" ref={conversation}>
        {messages.map((message, index) => (
          <div className={`chat-message ${message.sender === 'You' ? 'from-user' : ''}`} key={index}>
            <strong>{message.sender}</strong>
            <p role={message.error ? 'alert' : undefined}>{message.text}</p>
            {message.filters && (
              <p className="interpreted-request">
                Filters: {message.filters.category ?? 'any category'}
                {message.filters.date ? ` on ${message.filters.date}` : ' · any date'}
              </p>
            )}
            {message.events?.length > 0 && (
              <ul className="chat-event-results">
                {message.events.map((match) => (
                  <li key={match.id}>
                    <article aria-label={`Matched event: ${match.title}`}>
                      <h3>{match.title}</h3>
                      <p><span className="category-badge">{match.category}</span></p>
                      <p>{match.date} · {match.time} (Boston local time)</p>
                      <p>{match.location}</p>
                      <details>
                        <summary>View sample details</summary>
                        <p>{match.description}</p>
                      </details>
                    </article>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
        {isSending && <p role="status">Searching sample events…</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <label htmlFor="chat-request">Filter conditions (JSON)</label>
        <input
          id="chat-request"
          type="text"
          placeholder={'{"category":"Music","date":"2026-11-01"}'}
          maxLength={1000}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <div className="buttons">
          <button className="primary-button" type="submit" disabled={!draft.trim() || isSending}>
            {isSending ? 'Filtering…' : 'Filter sample events'}
          </button>
          <button className="text-button" type="button" onClick={clearChat}>Clear chat</button>
        </div>
      </form>
    </section>
  );
}
