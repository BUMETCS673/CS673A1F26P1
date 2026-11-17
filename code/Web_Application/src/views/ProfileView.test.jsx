// @vitest-environment jsdom
// AI-USAGE SUMMARY
// Authors: Daniel Winnie (taking over FV-103 from the Iteration 2 plan)
// Tools: Claude Code (Claude Opus), prompted by Daniel Winnie
// Overall AI Contribution: ~90%
// AI-Assisted Areas: Profile page tests (FV-103)
// Human Contributions: Daniel Winnie: requirements and prompts, chose the cases, reviewed every change before committing
// Notes/Verification: npm test

import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import ProfileView from './ProfileView.jsx';
import { createBackend } from '../testSupport/fakeBackend.js';

let backend;
const ALEX = { id: 1, username: 'alex', display_name: 'Alex', email: 'alex@example.com', activity_preferences: ['Music'] };
beforeEach(() => {
  backend = createBackend();
  backend.signedIn = 1;
  vi.stubGlobal('fetch', vi.fn(backend.fetch));
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

const nameField = () => screen.getByLabelText('Display name');
const box = (name) => screen.getByRole('checkbox', { name });
const saveButton = () => screen.getByRole('button', { name: /Save changes|Saving…/ });
const patches = () => backend.calls.filter((call) => call.method === 'PATCH');

describe('ProfileView', () => {
  it('shows the account and the current profile', () => {
    render(<ProfileView user={ALEX} />);
    expect(screen.getByText('@alex')).toBeTruthy();
    expect(screen.getByText('alex@example.com')).toBeTruthy();
    expect(nameField().value).toBe('Alex');
    expect(box('Music').checked).toBe(true);
    expect(box('Arts').checked).toBe(false);
    // Nothing changed yet, so there is nothing to save.
    expect(saveButton().disabled).toBe(true);
  });

  it('saves a new display name and preferences, and reports the updated account', async () => {
    const onUserChange = vi.fn();
    render(<ProfileView user={ALEX} onUserChange={onUserChange} />);
    fireEvent.change(nameField(), { target: { value: '  Alex P.  ' } });
    fireEvent.click(box('Social'));
    fireEvent.click(box('Arts'));
    fireEvent.click(saveButton());
    expect((await screen.findByRole('status')).textContent).toBe('Profile saved.');
    // Sent in the standard order, whatever order they were clicked in.
    expect(patches()[0].body).toEqual({ display_name: 'Alex P.', activity_preferences: ['Music', 'Arts', 'Social'] });
    expect(onUserChange).toHaveBeenCalledWith(expect.objectContaining({
      display_name: 'Alex P.', activity_preferences: ['Music', 'Arts', 'Social'],
    }));
    expect(nameField().value).toBe('Alex P.');
  });

  it('never sends username, email, or an account ID', async () => {
    render(<ProfileView user={ALEX} />);
    fireEvent.click(box('Food'));
    fireEvent.click(saveButton());
    await screen.findByRole('status');
    expect(Object.keys(patches()[0].body).sort()).toEqual(['activity_preferences', 'display_name']);
    expect(patches()[0].path).toBe('/api/auth/me');
  });

  it('requires a display name before sending anything', async () => {
    render(<ProfileView user={ALEX} />);
    fireEvent.change(nameField(), { target: { value: '   ' } });
    fireEvent.click(saveButton());
    expect(screen.getByRole('alert').textContent).toBe('Display name is required.');
    expect(document.activeElement).toBe(nameField());
    expect(patches()).toEqual([]);
  });

  it('requires at least one preference before sending anything', async () => {
    render(<ProfileView user={ALEX} />);
    fireEvent.click(box('Music'));
    fireEvent.click(saveButton());
    expect(screen.getByRole('alert').textContent).toBe('Choose at least one activity preference.');
    expect(document.activeElement).toBe(box('Music'));
    expect(patches()).toEqual([]);
  });

  it("shows the server's message when saving fails, and keeps the edits", async () => {
    render(<ProfileView user={ALEX} />);
    backend.failNext('PATCH', '/api/auth/me', 503);
    fireEvent.change(nameField(), { target: { value: 'Lex' } });
    fireEvent.click(saveButton());
    expect((await screen.findByRole('alert')).textContent).toBe('Simulated 503 failure.');
    expect(nameField().value).toBe('Lex');
    fireEvent.click(saveButton());
    expect((await screen.findByRole('status')).textContent).toBe('Profile saved.');
  });

  it('disables Save while saving, so a double click sends one request', async () => {
    render(<ProfileView user={ALEX} />);
    const release = backend.hold('PATCH', '/api/auth/me');
    fireEvent.change(nameField(), { target: { value: 'Lex' } });
    fireEvent.click(saveButton());
    fireEvent.click(saveButton());
    await waitFor(() => expect(saveButton().textContent).toBe('Saving…'));
    release();
    await screen.findByRole('status');
    expect(patches()).toHaveLength(1);
  });

  it('keeps markup in a display name as plain text', async () => {
    const { container } = render(<ProfileView user={{ ...ALEX, display_name: '<img src=x onerror=alert(1)>' }} />);
    expect(nameField().value).toBe('<img src=x onerror=alert(1)>');
    expect(container.querySelector('img')).toBeNull();
  });
});
