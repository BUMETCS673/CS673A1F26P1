// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: fetch wrappers for the Python API
// Human Contributions: Daniel Winnie: requirements and prompts, design choices (FastAPI, Docker layout, beginner-friendly comments), reviewed every change before committing, decided what to keep
// Notes/Verification: manual browser testing on localhost:3000 (desktop and narrow widths)

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

export const getEvents = () => request('/api/events');
export const getCurrentUser = () => request('/api/auth/me');
export const register = (account) => request('/api/auth/register', { method: 'POST', body: account });
export const logIn = (credentials) => request('/api/auth/login', { method: 'POST', body: credentials });
export const logOut = () => request('/api/auth/logout', { method: 'POST' });
