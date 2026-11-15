// AI-USAGE SUMMARY
// Authors: Daniel Winnie (scaffold, FV-125 integration), Ji Wu (earlier parse/filter demo actions)
// Tools: OpenAI Codex (CLI agent), prompted by Daniel Winnie; OpenAI Codex, prompted by Ji Wu (FV-117/118 demo actions); Claude Code (Claude Opus), prompted by Daniel Winnie (FV-125 chat integration)
// Overall AI Contribution: ~90%
// AI-Assisted Areas: chat panel scaffold; FV-125: send requests to POST /api/chat and show RecommendationResults
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep; Ji Wu: requirements and review of the earlier demo actions this replaces
// Notes/Verification: src/components/ChatPanel.test.jsx (npm test); manual browser testing on localhost:3000

import React, { useEffect, useRef, useState } from 'react';
import RecommendationResults from './RecommendationResults.jsx';
import { sendChat } from '../api.js';

const WELCOME = {
  sender: 'Assistant',
  text: "Ask for Boston events in your own words, for example 'music this friday after 6pm' "
    + "or 'food near North End'. Categories: Music, Arts, Food, Outdoors, Social.",
};

/**
 * The event chat. Each request goes to POST /api/chat; the reply is shown as event
 * cards, a clarification prompt, or a no-matches message (RecommendationResults).
 *
 * Props:
 *   onEventSelect  called with an event ID when a result card is clicked
 */
export default function ChatPanel({ onEventSelect }) {
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState([WELCOME]);
  const [isSending, setIsSending] = useState(false);
  const pendingRequest = useRef(null);
  const conversation = useRef(null);

  useEffect(() => () => pendingRequest.current?.abort(), []);
  useEffect(() => {
    if (conversation.current) {
      conversation.current.scrollTop = conversation.current.scrollHeight;
    }
  }, [messages, isSending]);

  async function send(text) {
    const request = text.trim();
    if (!request || pendingRequest.current) return;
    const controller = new AbortController();
    pendingRequest.current = controller;
    const timeout = setTimeout(() => controller.abort('timeout'), 15000);
    setMessages((previous) => [...previous, { sender: 'You', text: request }]);
    setDraft('');
    setIsSending(true);
    try {
      const response = await sendChat(request, controller.signal);
      if (controller.signal.aborted) return;
      setMessages((previous) => [...previous, { sender: 'Assistant', response }]);
    } catch (error) {
      // Clearing the chat or logging out cancels silently; show other failures.
      if (controller.signal.aborted && controller.signal.reason !== 'timeout') return;
      setMessages((previous) => [...previous, {
        sender: 'Assistant', error: true,
        text: controller.signal.aborted
          ? 'The server took too long to answer. Please try again.'
          : error.message,
      }]);
    } finally {
      clearTimeout(timeout);
      if (pendingRequest.current === controller) {
        pendingRequest.current = null;
        setIsSending(false);
      }
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    send(draft);
  }

  function clearChat() {
    pendingRequest.current?.abort();
    pendingRequest.current = null;
    setIsSending(false);
    setMessages([WELCOME]);
    setDraft('');
  }

  return (
    <section className="panel chat-panel" aria-labelledby="chat-title">
      <div className="section-heading">
        <h2 id="chat-title">Plan with a chat</h2>
      </div>
      <p className="muted-text">Describe what you want · results from the fictional Boston catalog</p>
      <div className="chat-messages" role="log" aria-label="Event conversation" ref={conversation}>
        {messages.map((message, index) => (
          <div className={`chat-message ${message.sender === 'You' ? 'from-user' : ''}`} key={index}>
            <strong>{message.sender}</strong>
            {message.text && <p role={message.error ? 'alert' : undefined}>{message.text}</p>}
            {message.response && (
              <RecommendationResults
                response={message.response}
                onEventSelect={onEventSelect}
                onSuggestion={isSending ? undefined : send}
              />
            )}
          </div>
        ))}
        {isSending && <p role="status">Finding events…</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <label htmlFor="chat-request">Your request</label>
        <input
          id="chat-request"
          type="text"
          placeholder="music this friday after 6pm"
          maxLength={1000}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <div className="buttons">
          <button className="primary-button" type="submit" disabled={!draft.trim() || isSending}>
            {isSending ? 'Sending…' : 'Send'}
          </button>
          <button className="text-button" type="button" onClick={clearChat}>Clear chat</button>
        </div>
      </form>
    </section>
  );
}
