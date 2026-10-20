import React, { useState } from 'react';

// These are fixed examples, not results from an AI or a movie API.
// Keeping the data here makes the first version easy to read and change.
const sampleMovies = [
  {
    title: 'Toy Story',
    year: 1995,
    genre: 'Animation / Adventure',
    description: 'A cowboy toy meets a new space ranger toy.',
  },
  {
    title: 'Finding Nemo',
    year: 2003,
    genre: 'Animation / Adventure',
    description: 'A father fish crosses the ocean to find his son.',
  },
  {
    title: 'WALL-E',
    year: 2008,
    genre: 'Animation / Science fiction',
    description: 'A small robot discovers a new purpose beyond cleaning Earth.',
  },
];

const welcomeMessage = {
  sender: 'Bot',
  text: 'What would you like to watch? Tell me a genre, mood, year, or runtime.',
};

// A component is a function that returns the part of the page it displays.
export default function App() {
  // State is information React remembers. Calling a setter redraws the page.
  // draft holds the input text; messages holds the conversation as an array.
  const [draft, setDraft] = useState('');
  const [messages, setMessages] = useState([welcomeMessage]);

  function handleSubmit(event) {
    // Forms normally reload the page. Prevent that so our chat stays visible.
    event.preventDefault();
    const request = draft.trim(); // Remove spaces at either end.
    if (request === '') return; // Do not add an empty message.

    // ... copies the existing array, then we add the two new messages.
    // The callback receives the latest state, even after rapid updates.
    setMessages((previousMessages) => [
      ...previousMessages,
      { sender: 'You', text: request },
      {
        sender: 'Bot',
        text: 'This demo shows the same three sample movies for every request. Personalized recommendations and preference recognition will be added later.',
      },
    ]);
    // Future step: send request to a backend chat endpoint and use its reply.
    // The current Python server has no chat endpoint yet. Keep API keys there,
    // on the server, rather than putting them in this browser code.
    setDraft(''); // Empty the input after sending.
  }

  function clearChat() {
    setMessages([welcomeMessage]);
    setDraft('');
  }

  // JSX looks like HTML. Braces { } insert JavaScript values or expressions.
  return (
    <main>
      <h1>AI Movie Recommendation Chat Bot</h1>
      <p>Describe what you want to watch and discover movies.</p>
      <p className="demo-note">Frontend demo: sample replies only. AI is not connected yet.</p>

      <section aria-labelledby="chat-heading">
        <h2 id="chat-heading">Chat</h2>
        {/* role="log" lets screen readers announce new chat messages. */}
        <div className="chat-messages" role="log" aria-label="Conversation">
          {/* map turns each message in the array into a paragraph. */}
          {messages.map((message, index) => (
            // An index is enough here because messages only append or reset.
            <p key={index}>
              <strong>{message.sender}:</strong> {message.text}
            </p>
          ))}
        </div>

        {/* A form lets the user click Send or press Enter. */}
        <form onSubmit={handleSubmit}>
          <label htmlFor="movie-request">What would you like to watch?</label>
          <input
            id="movie-request"
            type="text"
            placeholder="For example: a funny movie under two hours"
            value={draft}
            // Keep React's draft state in sync with what the user types.
            onChange={(event) => setDraft(event.target.value)}
          />
          <div className="buttons">
            <button type="submit" disabled={draft.trim() === ''}>Send</button>
            {/* type="button" prevents Clear chat from submitting the form. */}
            <button type="button" onClick={clearChat}>Clear chat</button>
          </div>
        </form>
      </section>

      {/* && shows this section only after the user sends a message. */}
      {messages.length > 1 && (
        <section aria-labelledby="movies-heading">
          <h2 id="movies-heading">Sample recommendations</h2>
          <p>These examples do not change based on your request.</p>
          {sampleMovies.map((movie) => (
            <article className="movie" key={movie.title}>
              <h3>{movie.title} ({movie.year})</h3>
              <p>{movie.genre}</p>
              <p>{movie.description}</p>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}
