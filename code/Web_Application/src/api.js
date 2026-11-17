
 // AI-USAGE SUMMARY
 // Authors: Daniel Winnie, Jibek Kelgenbaeva
 // Tools: Claude Code (Claude Opus), prompted by Daniel Winnie; ChatGPT (OpenAI), prompted by Jibek Kelgenbaeva (FV-122/FV-123)
 // Overall AI Contribution: ~90% (Daniel's parts); 90% (Jibek's FV-122/FV-123 parts)
 // AI-Assisted Areas: fetch wrappers for the Python API, paginated event requests, and event-details API requests
 // Human Contributions: Daniel Winnie: requirements, prompts, FastAPI integration design, and review; Jibek Kelgenbaeva: FV-122/FV-123 API integration requirements, testing, and verification
 // Notes/Verification: manual browser testing and FV-122/FV-123 API integration verification

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

export const getEvents = (limit = 5, offset = 0) =>
  request(`/api/events?limit=${limit}&offset=${offset}`);

export const getEventById = (id) =>
  request(`/api/events/${encodeURIComponent(id)}`);

export const getCurrentUser = () => request('/api/auth/me');
export const register = (account) => request('/api/auth/register', { method: 'POST', body: account });
export const logIn = (credentials) => request('/api/auth/login', { method: 'POST', body: credentials });
export const logOut = () => request('/api/auth/logout', { method: 'POST' });
