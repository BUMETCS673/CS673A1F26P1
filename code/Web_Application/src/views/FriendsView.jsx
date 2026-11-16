// AI-USAGE SUMMARY
// Author: Junshuo Huang
// Tool: OpenAI Codex
// Overall AI Contribution: 100% of the initial code draft.
// AI-Assisted Areas: connecting search, follower lists, and follow actions to the API.
// Human Contributions: Junshuo Huang supplied the one-way follow and follow-back requirements.
// Notes/Verification: Vite build and frontend tests with mocked API responses.

import React, { useEffect, useState } from 'react';
import { followUser, getFollowers, getFollowing, searchUsers, unfollowUser } from '../api.js';
import './FriendsView.css';

function AccountRow({ account, following, followsYou, disabled, onToggle }) {
  const action = following ? 'Unfollow' : followsYou ? 'Follow back' : 'Follow';
  const relationship = following && followsYou ? 'Mutual' : following ? 'Following' : 'Follows you';

  return (
    <div className="friends-row">
      <div>
        <strong>{account.display_name || account.username}</strong>
        <p className="muted-text">@{account.username}</p>
        {(following || followsYou) && <span className="category-badge">{relationship}</span>}
      </div>
      <button
        className={following ? 'secondary-button' : 'primary-button'}
        type="button"
        aria-label={`${action} @${account.username}`}
        disabled={disabled}
        onClick={() => onToggle(account)}
      >
        {action}
      </button>
    </div>
  );
}

function PeopleList({ accounts, emptyMessage, renderAccount }) {
  return accounts.length === 0 ? (
    <p className="muted-text">{emptyMessage}</p>
  ) : (
    <ul className="friends-list">
      {accounts.map((account) => <li key={account.id}>{renderAccount(account)}</li>)}
    </ul>
  );
}

export default function FriendsView() {
  const [following, setFollowing] = useState([]);
  const [followers, setFollowers] = useState([]);
  const [listStatus, setListStatus] = useState('loading');
  const [listError, setListError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [username, setUsername] = useState('');
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let mounted = true;
    Promise.all([getFollowing(), getFollowers()])
      .then(([followingAccounts, followerAccounts]) => {
        if (!mounted) return;
        setFollowing(followingAccounts);
        setFollowers(followerAccounts);
        setListStatus('ready');
      })
      .catch((error) => {
        if (!mounted) return;
        setListError(error.message);
        setListStatus('error');
      });
    return () => { mounted = false; };
  }, [attempt]);

  function retryLists() {
    setListStatus('loading');
    setAttempt((previous) => previous + 1);
  }

  async function handleSearch(event) {
    event.preventDefault();
    if (searching) return;
    setSearchError('');
    setResults(null);
    const query = username.trim();
    if (query === '') {
      setSearchError('Enter a username to search.');
      return;
    }
    setSearching(true);
    try {
      setResults(await searchUsers(query));
    } catch (error) {
      setSearchError(error.message);
    } finally {
      setSearching(false);
    }
  }

  async function toggleFollow(account) {
    if (saving || listStatus !== 'ready') return;
    const wasFollowing = following.some((person) => person.id === account.id);

    setSaving(true);
    setActionError('');
    setNotice('');
    try {
      if (wasFollowing) {
        await unfollowUser(account.id);
        setFollowing((previous) => previous.filter((person) => person.id !== account.id));
        setNotice(`Unfollowed @${account.username}.`);
      } else {
        await followUser(account.id);
        setFollowing((previous) => [...previous, account].sort((a, b) =>
          a.username.localeCompare(b.username, 'en', { sensitivity: 'base' })
        ));
        setNotice(`Now following @${account.username}.`);
      }
    } catch (error) {
      setActionError(error.message);
    } finally {
      setSaving(false);
    }
  }

  function renderAccount(account) {
    return (
      <AccountRow
        account={account}
        following={following.some((person) => person.id === account.id)}
        followsYou={followers.some((person) => person.id === account.id)}
        disabled={saving || listStatus !== 'ready'}
        onToggle={toggleFollow}
      />
    );
  }

  return (
    <main className="dashboard friends-view">
      <header className="page-heading">
        <h1>Friends</h1>
      </header>
      <section className="panel" aria-labelledby="friends-search-heading">
        <h2 id="friends-search-heading">Find people</h2>
        <form onSubmit={handleSearch}>
          <label htmlFor="friends-username">Username</label>
          <div className="friends-search">
            <input
              id="friends-username"
              type="search"
              maxLength={50}
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
            <button className="primary-button" disabled={searching} type="submit">
              {searching ? 'Searching…' : 'Search'}
            </button>
          </div>
        </form>
        {searchError && <p role="alert">{searchError}</p>}
        {results && (
          <PeopleList
            accounts={results}
            emptyMessage="No account found with that username."
            renderAccount={renderAccount}
          />
        )}
      </section>
      {actionError && <p role="alert">{actionError}</p>}
      {notice && <p role="status">{notice}</p>}
      {listStatus === 'loading' && <p role="status">Loading follow lists…</p>}
      {listStatus === 'error' && (
        <div className="panel">
          <p role="alert">{listError}</p>
          <button className="secondary-button" type="button" onClick={retryLists}>Retry</button>
        </div>
      )}
      {listStatus === 'ready' && (
        <div className="friends-columns">
          <section className="panel" aria-labelledby="friends-following-heading">
            <h2 id="friends-following-heading">Following ({following.length})</h2>
            <PeopleList accounts={following} emptyMessage="You aren’t following anyone yet." renderAccount={renderAccount} />
          </section>
          <section className="panel" aria-labelledby="friends-followers-heading">
            <h2 id="friends-followers-heading">Followers ({followers.length})</h2>
            <PeopleList accounts={followers} emptyMessage="You don’t have any followers yet." renderAccount={renderAccount} />
          </section>
        </div>
      )}
    </main>
  );
}
