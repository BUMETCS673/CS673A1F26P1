// AI-USAGE SUMMARY
// Authors: Daniel Winnie (taking over FV-95 from the Iteration 2 plan)
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: shared My Plans state for the Save buttons and the My Plans view (FV-95)
// Human Contributions: Daniel Winnie: requirements and prompts, design choices, reviewed every change before committing, decided what to keep
// Notes/Verification: src/plans.test.jsx, src/views/MyPlansView.test.jsx (npm test); browser check with two accounts

// One copy of the signed-in user's plans, shared by every Save button (event
// details, chat cards) and the My Plans view, so saving in one place updates the
// others immediately. App.jsx mounts one PlansProvider per signed-in account.

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { getPlans, removePlan, savePlan } from './api.js';

const PlansContext = createContext(null);

// `enabled` is false while nobody is signed in, so no request is sent then.
export function PlansProvider({ enabled = true, children }) {
  // status: 'loading' | 'ready' | 'error'. `plans` is the last list the server sent.
  const [listing, setListing] = useState({ status: 'loading', plans: [], unavailableCount: 0 });
  // IDs known to be saved. Updated as soon as a save/remove succeeds, even if the
  // following list refresh fails, so a Save button never shows the wrong state.
  const [savedIds, setSavedIds] = useState(() => new Set());
  const [pendingIds, setPendingIds] = useState(() => new Set());
  const latestLoad = useRef(0);

  const reload = useCallback(async () => {
    // Only the newest refresh may update the list, if two answers arrive out of order.
    const loadNumber = ++latestLoad.current;
    setListing((previous) => ({ ...previous, status: previous.status === 'ready' ? 'ready' : 'loading' }));
    try {
      const data = await getPlans();
      if (loadNumber !== latestLoad.current) return;
      setListing({ status: 'ready', plans: data.plans, unavailableCount: data.unavailable_count });
      setSavedIds(new Set(data.plans.map((plan) => plan.event.id)));
    } catch {
      if (loadNumber === latestLoad.current) setListing((previous) => ({ ...previous, status: 'error' }));
    }
  }, []);

  useEffect(() => { if (enabled) reload(); }, [enabled, reload]);

  const track = useCallback(async (eventId, action) => {
    setPendingIds((previous) => new Set(previous).add(eventId));
    try {
      await action();
    } finally {
      setPendingIds((previous) => {
        const next = new Set(previous);
        next.delete(eventId);
        return next;
      });
    }
  }, []);

  // Both throw the server's message (e.g. "This event has already ended.") so the
  // button that was clicked can show it.
  const save = useCallback((eventId) => track(eventId, async () => {
    await savePlan(eventId);
    setSavedIds((previous) => new Set(previous).add(eventId));
    reload();
  }), [track, reload]);

  const remove = useCallback((eventId) => track(eventId, async () => {
    await removePlan(eventId);
    setSavedIds((previous) => {
      const next = new Set(previous);
      next.delete(eventId);
      return next;
    });
    setListing((previous) => ({
      ...previous, plans: previous.plans.filter((plan) => plan.event.id !== eventId),
    }));
    // Also discards any refresh that started before the removal and would bring it back.
    reload();
  }), [track, reload]);

  const value = useMemo(
    () => ({ ...listing, savedIds, pendingIds, reload, save, remove }),
    [listing, savedIds, pendingIds, reload, save, remove],
  );
  return <PlansContext.Provider value={value}>{children}</PlansContext.Provider>;
}

// null outside a PlansProvider (e.g. the standalone previews), so callers can hide
// plan controls there.
export function usePlans() {
  return useContext(PlansContext);
}
