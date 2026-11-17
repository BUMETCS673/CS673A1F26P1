// AI-USAGE SUMMARY
// Author: Junshuo Huang
// Tool: OpenAI Codex
// Overall AI Contribution: 100% of the initial code draft.
// AI-Assisted Areas: connecting search, follower lists, and follow actions to the API.
// Human Contributions: Junshuo Huang supplied the one-way follow and follow-back requirements.
// Notes/Verification: Vite build and frontend tests with mocked API responses.
// Friends' plans (Daniel Winnie, taking over "friends going" from the Iteration 2 plan): Claude Code (Claude Opus), ~90%;
// "See plans" for mutual follows and the friend's upcoming plans panel. Verified with src/views/FriendsView.test.jsx and a three-account browser check.

import React, { useEffect, useState } from 'react';
import { followUser, getFollowers, getFollowing, getFriendPlans, searchUsers, unfollowUser } from '../api.js';
import { formatBostonTimeRange } from '../recommendations.js';
import { personName } from '../friendsGoing.js';
import './FriendsView.css';

function AccountRow({ account, following, followsYou, disabled, onToggle, onShowPlans }) {
  const action = following ? 'Unfollow' : followsYou ? 'Follow back' : 'Follow';
  const relationship = following && followsYou ? 'Mutual' : following ? 'Following' : 'Follows you';

  return (
    <div className="friends-row">
      <div>
        <strong>{account.display_name || account.username}</strong>
        <p className="muted-text">@{account.username}</p>
        {(following || followsYou) && <span className="category-badge">{relationship}</span>}
      </div>
      <div className="friends-row-actions">
        {following && followsYou && onShowPlans && (
          <button
            className="secondary-button"
            type="button"
            aria-label={`See plans of @${account.username}`}
            onClick={() => onShowPlans(account)}
          >
            See plans
          </button>
        )}
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

// A mutual follow's upcoming saved events. Each one opens its details on the Events page.
function FriendPlans({ friend, onEventSelect, onClose }) {
  const [state, setState] = useState({ status: 'loading', plans: [] });

  useEffect(() => {
    let current = true;
    setState({ status: 'loading', plans: [] });
    getFriendPlans(friend.id)
      .then((data) => { if (current) setState({ status: 'ready', plans: data.plans }); })
      .catch((error) => {
        if (!current) return;
        const message = error.status === 404
          ? `You can see ${personName(friend)}'s plans only while you follow each other.`
          : error.message;
        setState({ status: 'error', plans: [], message });
      });
    return () => { current = false; };
  }, [friend.id]);

  const name = personName(friend);
  return (
    <section className="panel friend-plans" aria-labelledby="friend-plans-heading">
      <div className="section-heading">
        <h2 id="friend-plans-heading">{name}'s upcoming plans</h2>
        <button className="text-button" type="button" onClick={onClose}>Close</button>
      </div>
      {state.status === 'loading' && <p role="status">Loading {name}'s plans…</p>}
      {state.status === 'error' && <p role="alert">{state.message}</p>}
      {state.status === 'ready' && (state.plans.length === 0 ? (
        <p className="muted-text">{name} has no upcoming plans.</p>
      ) : (
        <ul className="friends-list">
          {state.plans.map(({ event }) => (
            <li className="friends-row" key={event.id}>
              <div>
                <strong>{event.title}</strong>
                <p className="muted-text">{formatBostonTimeRange(event.start, event.end)}</p>
                <p className="muted-text">{event.location || 'Location unavailable'}</p>
              </div>
              <button
                className="secondary-button"
                type="button"
                aria-label={`View details: ${event.title}`}
                onClick={() => onEventSelect?.(event.id)}
              >
                View details
              </button>
            </li>
          ))}
        </ul>
      ))}
    </section>
  );
}

/**
 * Props:
 *   onEventSelect  called with an event ID to show its details on the Events page
 */
export default function FriendsView({ onEventSelect }) {
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
  const [planFriend, setPlanFriend] = useState(null);

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
        // No longer mutual, so their plans are no longer visible.
        if (planFriend?.id === account.id) setPlanFriend(null);
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
        onShowPlans={setPlanFriend}
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
      {planFriend && (
        <FriendPlans
          key={planFriend.id}
          friend={planFriend}
          onEventSelect={onEventSelect}
          onClose={() => setPlanFriend(null)}
        />
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
