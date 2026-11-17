// AI-USAGE SUMMARY
// Authors: Daniel Winnie
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: in-memory stand-in for the Python API used by frontend tests (FV-95 onward)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: used by the *.test.jsx files (npm test)

// A small in-memory version of the Python API, so component tests can click through
// whole flows (sign in, save, open My Plans, remove...) the way a person would.
// It follows the same rules as the real routes; tests/live_*.py check those rules
// against PostgreSQL. Install it with `vi.stubGlobal('fetch', backend.fetch)`.

export const EVENTS = [
  {
    id: 'sample-1', title: 'Acoustic evening in Back Bay', category: 'Music',
    start: '2026-11-21T18:00:00-05:00', end: '2026-11-21T20:00:00-05:00',
    location: 'Back Bay, Boston', description: 'Fictional acoustic sets.',
  },
  {
    id: 'sample-2', title: 'Late jazz in the South End', category: 'Music',
    // 11:30 PM in Boston is already Nov 22 in UTC; it still belongs to Saturday.
    start: '2026-11-21T23:30:00-05:00', end: '2026-11-22T01:00:00-05:00',
    location: 'South End, Boston', description: 'Fictional late set.',
  },
  {
    id: 'sample-3', title: 'North End food walk', category: 'Food',
    start: '2026-11-22T12:00:00-05:00', end: '2026-11-22T14:00:00-05:00',
    location: 'North End, Boston', description: 'Fictional tasting walk.',
  },
  {
    id: 'sample-4', title: 'Harbor sunrise run', category: 'Outdoors',
    start: '2026-12-05T07:00:00-05:00', end: '2026-12-05T08:30:00-05:00',
    location: null, description: 'Fictional run.',
  },
  {
    id: 'past-1', title: 'Last week gallery night', category: 'Arts',
    start: '2026-11-08T18:00:00-05:00', end: '2026-11-08T20:00:00-05:00',
    location: 'SoWa, Boston', description: 'Already ended.',
  },
  {
    id: 'past-2', title: 'Yesterday board games', category: 'Social',
    start: '2026-11-16T19:00:00-05:00', end: '2026-11-16T22:00:00-05:00',
    location: 'Fenway, Boston', description: 'Already ended.',
  },
];

export const NOW = new Date('2026-11-17T12:00:00-05:00');

function json(body, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), {
    status, headers: { 'Content-Type': 'application/json' },
  }));
}
const noContent = () => Promise.resolve(new Response(null, { status: 204 }));

export function createBackend({ events = EVENTS, now = () => NOW } = {}) {
  const backend = {
    users: [
      { id: 1, username: 'alex', display_name: 'Alex', email: 'alex@example.com', activity_preferences: ['Music'], password: 'alex password' },
      { id: 2, username: 'sam', display_name: 'Sam', email: 'sam@example.com', activity_preferences: ['Food'], password: 'sam password' },
      { id: 3, username: 'pat', display_name: null, email: 'pat@example.com', activity_preferences: ['Arts'], password: 'pat password' },
      { id: 4, username: 'bea', display_name: 'Bea', email: 'bea@example.com', activity_preferences: ['Social'], password: 'bea password' },
    ],
    signedIn: null,            // user id of the session cookie, or null
    events: events.map((event) => ({ ...event })),  // copies, so tests can edit them
    plans: new Map(),          // user id -> Map(event id -> saved_at)
    follows: new Set(),        // "followerId:followedId"
    failures: new Map(),       // "METHOD path" -> status, used once each
    calls: [],
    savedAtClock: Date.parse('2026-11-17T10:00:00Z'),
    // A request can be held until the test calls the returned release().
    holds: new Map(),
  };

  const ended = (event) => new Date(event.end) <= now();
  const publicUser = ({ password, ...user }) => user;
  const plansOf = (id) => {
    if (!backend.plans.has(id)) backend.plans.set(id, new Map());
    return backend.plans.get(id);
  };

  function route(method, path, url, body) {
    const me = backend.users.find((user) => user.id === backend.signedIn);
    if (method === 'POST' && path === '/api/auth/login') {
      const user = backend.users.find((u) => u.username === body.username && u.password === body.password);
      if (!user) return json({ detail: 'Incorrect username or password.' }, 401);
      backend.signedIn = user.id;
      return json(publicUser(user));
    }
    if (method === 'POST' && path === '/api/auth/logout') {
      backend.signedIn = null;
      return noContent();
    }
    if (!me) return json({ detail: 'Not logged in.' }, 401);

    if (method === 'GET' && path === '/api/auth/me') return json(publicUser(me));
    if (method === 'PATCH' && path === '/api/auth/me') {
      const allowed = ['display_name', 'activity_preferences'];
      const keys = Object.keys(body ?? {});
      if (keys.length === 0 || keys.some((key) => !allowed.includes(key))) {
        return json({ detail: [{ msg: 'Extra inputs are not permitted' }] }, 422);
      }
      if ('display_name' in body && !String(body.display_name ?? '').trim()) {
        return json({ detail: [{ msg: 'Value error, Display name is required.' }] }, 422);
      }
      if ('activity_preferences' in body && !body.activity_preferences?.length) {
        return json({ detail: [{ msg: 'Value error, Choose at least one activity preference.' }] }, 422);
      }
      if ('display_name' in body) me.display_name = body.display_name.trim();
      if ('activity_preferences' in body) me.activity_preferences = [...new Set(body.activity_preferences)];
      return json(publicUser(me));
    }

    if (method === 'GET' && path === '/api/events') {
      const limit = Number(url.searchParams.get('limit') ?? 10);
      const offset = Number(url.searchParams.get('offset') ?? 0);
      const upcoming = backend.events.filter((event) => !ended(event))
        .sort((a, b) => new Date(a.start) - new Date(b.start) || a.id.localeCompare(b.id));
      const next = offset + limit;
      return json({ events: upcoming.slice(offset, next), next_offset: next < upcoming.length ? next : null });
    }
    let match = /^\/api\/events\/([^/]+)$/.exec(path);
    if (method === 'GET' && match) {
      const event = backend.events.find((item) => item.id === decodeURIComponent(match[1]));
      return event ? json(event) : json({ detail: 'Event not found' }, 404);
    }

    if (method === 'GET' && path === '/api/plans') {
      const saved = plansOf(me.id);
      const found = backend.events.filter((event) => saved.has(event.id))
        .sort((a, b) => new Date(a.start) - new Date(b.start) || a.id.localeCompare(b.id));
      return json({
        plans: found.map((event) => ({ event, saved_at: saved.get(event.id), ended: ended(event) })),
        unavailable_count: saved.size - found.length,
      });
    }
    match = /^\/api\/plans\/(.+)$/.exec(path);
    if (match) {
      const id = decodeURIComponent(match[1]);
      if (method === 'PUT') {
        const event = backend.events.find((item) => item.id === id);
        if (!event) return json({ detail: 'Event not found' }, 404);
        if (ended(event)) return json({ detail: 'This event has already ended.' }, 409);
        if (!plansOf(me.id).has(id)) {
          backend.savedAtClock += 60_000;
          plansOf(me.id).set(id, new Date(backend.savedAtClock).toISOString());
        }
        return noContent();
      }
      if (method === 'DELETE') {
        plansOf(me.id).delete(id);
        return noContent();
      }
    }

    const mutual = (a, b) => backend.follows.has(`${a}:${b}`) && backend.follows.has(`${b}:${a}`);
    match = /^\/api\/events\/(.+)\/friends-going$/.exec(path);
    if (method === 'GET' && match) {
      const id = decodeURIComponent(match[1]);
      if (!backend.events.some((event) => event.id === id)) return json({ detail: 'Event not found' }, 404);
      // Sorted by username, like the SQL.
      const friends = backend.users.filter((u) => u.id !== me.id && mutual(me.id, u.id) && plansOf(u.id).has(id))
        .sort((a, b) => a.username.localeCompare(b.username));
      return json({ friends: friends.map(({ id: userId, username, display_name }) => ({ id: userId, username, display_name })) });
    }
    match = /^\/api\/friends\/(\d+)\/plans$/.exec(path);
    if (method === 'GET' && match) {
      const friend = backend.users.find((u) => u.id === Number(match[1]));
      if (!friend || friend.id === me.id || !mutual(me.id, friend.id)) return json({ detail: 'Friend not found' }, 404);
      const upcoming = backend.events.filter((event) => plansOf(friend.id).has(event.id) && !ended(event))
        .sort((a, b) => new Date(a.start) - new Date(b.start) || a.id.localeCompare(b.id));
      const { id: friendId, username, display_name } = friend;
      return json({ friend: { id: friendId, username, display_name }, plans: upcoming.map((event) => ({ event })) });
    }
    match = /^\/api\/following\/(\d+)$/.exec(path);
    if (match && method === 'PUT') { backend.follows.add(`${me.id}:${match[1]}`); return noContent(); }
    if (match && method === 'DELETE') { backend.follows.delete(`${me.id}:${match[1]}`); return noContent(); }
    if (method === 'GET' && path === '/api/users/search') {
      const name = url.searchParams.get('username').toLowerCase();
      return json(backend.users.filter((u) => u.username === name && u.id !== me.id).map(publicUser)
        .map(({ email, activity_preferences, ...rest }) => rest));
    }

    if (method === 'GET' && path === '/api/chat/history') return json({ messages: [] });
    if (method === 'POST' && path === '/api/chat') {
      // A tiny stand-in for the parser: a category word only (the real one is tested in Python).
      const category = ['Music', 'Arts', 'Food', 'Outdoors', 'Social']
        .find((name) => body.message.toLowerCase().includes(name.toLowerCase())) ?? null;
      const events = category === null ? [] : backend.events
        .filter((event) => event.category === category && !ended(event))
        .sort((a, b) => new Date(a.start) - new Date(b.start));
      return json({
        interpretation: {
          category, date: null, time: null, time_operator: null, location: null,
          location_operator: null, timezone: 'America/New_York', needs_clarification: category === null,
        },
        events,
      });
    }
    if (method === 'GET' && path === '/api/following') {
      return json(backend.users.filter((u) => backend.follows.has(`${me.id}:${u.id}`))
        .map(({ id, username, display_name }) => ({ id, username, display_name })));
    }
    if (method === 'GET' && path === '/api/followers') {
      return json(backend.users.filter((u) => backend.follows.has(`${u.id}:${me.id}`))
        .map(({ id, username, display_name }) => ({ id, username, display_name })));
    }
    return json({ detail: `fake backend has no route for ${method} ${path}` }, 500);
  }

  backend.fetch = async (input, options = {}) => {
    const method = options.method ?? 'GET';
    const url = new URL(input, 'http://localhost');
    const path = url.pathname;
    const body = options.body ? JSON.parse(options.body) : undefined;
    backend.calls.push({ method, path: `${path}${url.search}`, body });
    const key = `${method} ${path}`;
    if (backend.holds.has(key)) await backend.holds.get(key).promise;
    if (backend.failures.has(key)) {
      const { status, times } = backend.failures.get(key);
      if (times <= 1) backend.failures.delete(key);
      else backend.failures.set(key, { status, times: times - 1 });
      if (status === 'network') throw new TypeError('Failed to fetch');
      return json({ detail: `Simulated ${status} failure.` }, status);
    }
    return route(method, path, url, body);
  };

  // Make the next `times` `METHOD path` requests fail with this status ('network' to throw).
  backend.failNext = (method, path, status, times = 1) =>
    backend.failures.set(`${method} ${path}`, { status, times });
  // Hold every `METHOD path` request until release() is called.
  backend.hold = (method, path) => {
    let release;
    const promise = new Promise((resolve) => { release = resolve; });
    backend.holds.set(`${method} ${path}`, { promise });
    return () => { backend.holds.delete(`${method} ${path}`); release(); };
  };
  backend.callsTo = (method, path) => backend.calls.filter((call) => call.method === method && call.path === path);
  backend.savedIds = (userId) => [...plansOf(userId).keys()].sort();
  return backend;
}
