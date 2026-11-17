// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: fetch wrappers for the Python API (including sendChat, FV-125, and chat history, FV-121)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
// Notes/Verification: manual browser testing on localhost:3000 (desktop and narrow widths)

// Follow API wrappers (Junshuo Huang, FV-92): OpenAI Codex drafted the code from the existing API contract.
// Overall AI Contribution (FV-92): 100% of the initial code draft.
// Notes/Verification (FV-92): frontend tests with mocked API responses.

// Small wrappers around the Python API. Relative URLs go through Vite's /api proxy,
// and the browser sends the HttpOnly session cookie automatically.

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: options.body ? { 'Content-Type': 'application/json' } : undefined,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new Error('Could not reach the server. Check that the project is running, then try again.');
  }
  if (response.ok) return response.status === 204 ? null : response.json();

  const result = await response.json().catch(() => ({}));
  const error = new Error(errorMessage(result.detail));
  error.status = response.status;
  throw error;
}

// FastAPI returns a string, or for invalid fields a list of { msg } objects.
function errorMessage(detail) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg.replace(/^Value error, /, '');
  return 'Something went wrong. Please try again.';
}

export const searchUsers = (username) =>
  request(`/api/users/search?${new URLSearchParams({ username })}`);

export const getFollowing = () => request('/api/following');
export const getFollowers = () => request('/api/followers');
export const followUser = (id) => request(`/api/following/${id}`, { method: 'PUT' });
export const unfollowUser = (id) => request(`/api/following/${id}`, { method: 'DELETE' });

export const getEvents = (limit = 5, offset = 0) =>
  request(`/api/events?limit=${limit}&offset=${offset}`);

export const getEventById = (id) =>
  request(`/api/events/${encodeURIComponent(id)}`);

// FV-125: { interpretation, events } for a free-text request. `signal` lets the
// chat cancel a request when it is cleared or the user logs out.
export const sendChat = (message, signal) =>
  request('/api/chat', { method: 'POST', body: { message }, signal });

// FV-121: the signed-in user's last 50 exchanges, and "Clear history".
export const getChatHistory = () => request('/api/chat/history');
export const clearChatHistory = () => request('/api/chat/history', { method: 'DELETE' });

export const getCurrentUser = () => request('/api/auth/me');
export const register = (account) => request('/api/auth/register', { method: 'POST', body: account });
export const logIn = (credentials) => request('/api/auth/login', { method: 'POST', body: credentials });
export const logOut = () => request('/api/auth/logout', { method: 'POST' });
