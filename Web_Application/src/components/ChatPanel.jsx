import React, { useEffect, useRef, useState } from 'react';

const welcomeMessages = {
  parse: {
    sender: 'Assistant',
    text: "Try 'music' or 'Music on 2026-11-01'. Supported categories: Music, Arts, Food, Outdoors, Social. This action shows category, date, and needs_clarification. To filter the sample events, choose Filter sample events under Chat action.",
  },
  filter: {
    sender: 'Assistant',
    text: 'Enter JSON conditions, for example {"category":"Music","date":"2026-11-01"}. Use {"category":"Music"} for any date, {"date":"2026-11-01"} for any category, or {} for all samples. To parse text instead, choose Parse request under Chat action.',
  },
};

export default function ChatPanel({ events }) {
  const [mode, setMode] = useState('parse');
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState([welcomeMessages.parse]);
  const [isSending, setIsSending] = useState(false);
  const pendingRequest = useRef(null);
  const conversation = useRef(null);
  const isFilter = mode === 'filter';

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
    if (isFilter) {
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
          text: 'Enter a JSON object with only category and/or date, for example {"category":"Music","date":"2026-11-01"}. Choose Parse request to interpret text instead.',
        }]);
        return;
      }
    }
    const controller = new AbortController();
    pendingRequest.current = controller;
    const timeout = setTimeout(() => controller.abort('timeout'), 15000);
    setMessages((previous) => [...previous, { sender: 'You', text: request }]);
    setDraft('');
    setIsSending(true);
    try {
      // Parsing sends only text; filtering sends explicit conditions and samples.
      const response = await fetch(isFilter ? '/api/demo/filter-events' : '/api/demo/parse-event-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(isFilter ? { ...filters, events } : { message: request }),
        signal: controller.signal,
      });
      if (isFilter && response.status === 422) {
        throw new Error('Use category up to 50 characters and date up to 10 characters.');
      }
      if (!response.ok) throw new Error('Demo request failed');
      const result = await response.json();
      if (controller.signal.aborted) return;
      setMessages((previous) => [...previous, isFilter ? {
        sender: 'Assistant', text: result.message,
        filters: { category: result.category, date: result.date }, events: result.events,
      } : {
        sender: 'Assistant',
        text: result.needs_clarification
          ? "Please clarify: use Music, Arts, Food, Outdoors, or Social, optionally followed by 'on YYYY-MM-DD' with a valid date. Relative dates and other phrases are not supported."
          : 'Request recognized. Parsed conditions:',
        interpretation: result,
      }]);
    } catch (error) {
      // Clear chat, action changes, and logout cancel silently; show other failures.
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

  function resetChat(nextMode) {
    pendingRequest.current?.abort();
    pendingRequest.current = null;
    setIsSending(false);
    setMessages([welcomeMessages[nextMode]]);
    setDraft('');
  }

  function changeMode(event) {
    const nextMode = event.target.value;
    setMode(nextMode);
    resetChat(nextMode);
  }

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="section-heading">
        <h2 id="chat-title">Plan with a chat</h2>
        <span className="placeholder-badge">{isFilter ? 'Filter demo' : 'Parser demo'}</span>
      </div>
      <p className="muted-text">{isFilter
        ? 'Explicit JSON filters · sample events only'
        : 'Request parsing · choose Filter sample events to search the samples'}</p>
      <label htmlFor="chat-action">Chat action</label>
      <select id="chat-action" value={mode} onChange={changeMode}>
        <option value="parse">Parse request</option>
        <option value="filter">Filter sample events</option>
      </select>
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
        {isSending && <p role="status">{isFilter ? 'Searching sample events…' : 'Parsing request…'}</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <label htmlFor="chat-request">{isFilter ? 'Filter conditions (JSON)' : 'Request text'}</label>
        <input
          id="chat-request"
          type="text"
          placeholder={isFilter ? '{"category":"Music","date":"2026-11-01"}' : 'Music on 2026-11-01'}
          maxLength={1000}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <div className="buttons">
          <button className="primary-button" type="submit" disabled={!draft.trim() || isSending}>
            {isSending ? (isFilter ? 'Filtering…' : 'Parsing…') : (isFilter ? 'Filter sample events' : 'Parse request')}
          </button>
          <button className="text-button" type="button" onClick={() => resetChat(mode)}>Clear chat</button>
        </div>
      </form>
    </section>
  );
}
