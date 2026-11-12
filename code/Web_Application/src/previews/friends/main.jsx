// AI-USAGE SUMMARY
// Author: Junshuo Huang
// Tool: ChatGPT (Codex)
// AI-Assisted Areas: username search, follow state, and standalone React preview
// Human Contributions: Junshuo Huang defined the standalone Docker preview and follow-back workflow.

import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './friends.css';

const accounts = [
  { username: 'jordan', displayName: 'Jordan Lee' },
  { username: 'taylor', displayName: 'Taylor Kim' },
];

function AccountRow({ account, isFollowing, followsYou, onToggleFollow }) {
  let relationship = '';
  let action = 'Follow';
  if (isFollowing) {
    relationship = followsYou ? 'Mutual' : 'Following';
    action = 'Unfollow';
  } else if (followsYou) {
    relationship = 'Follows you';
    action = 'Follow back';
  }

  return (
    <div className="account-row">
      <div>
        <strong>{account.displayName}</strong>
        <p className="muted">@{account.username}</p>
        {relationship && <p className="relationship" role="status">{relationship}</p>}
      </div>
      <button
        className={isFollowing ? 'secondary' : undefined}
        type="button"
        aria-label={`${action} @${account.username}`}
        onClick={() => onToggleFollow(account.username)}
      >
        {action}
      </button>
    </div>
  );
}

function AccountList({ id, title, entries, emptyMessage, renderAccount }) {
  return (
    <section className="panel" aria-labelledby={id}>
      <h2 id={id}>{title} <span className="count">{entries.length}</span></h2>
      {entries.length === 0 ? (
        <p className="muted">{emptyMessage}</p>
      ) : (
        <ul className="account-list">
          {entries.map((account) => (
            <li key={account.username}>{renderAccount(account)}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function FriendsPreview() {
  const [currentUser, setCurrentUser] = useState(accounts[0].username);
  const [followingByUser, setFollowingByUser] = useState({
    jordan: [],
    taylor: [],
  });
  const [query, setQuery] = useState('');
  const [searchedUsername, setSearchedUsername] = useState(null);

  const following = accounts.filter((account) =>
    followingByUser[currentUser].includes(account.username)
  );
  const followers = accounts.filter((account) =>
    followingByUser[account.username].includes(currentUser)
  );
  const match = accounts.find((account) => account.username === searchedUsername);
  const result = searchedUsername === currentUser ? undefined : match;

  function switchUser(event) {
    setCurrentUser(event.target.value);
    setQuery('');
    setSearchedUsername(null);
  }

  function searchByUsername(event) {
    event.preventDefault();
    setSearchedUsername(query.trim().toLowerCase());
  }

  function toggleFollow(username) {
    setFollowingByUser((previous) => {
      const currentFollowing = previous[currentUser];
      const updated = currentFollowing.includes(username)
        ? currentFollowing.filter((followed) => followed !== username)
        : [...currentFollowing, username];

      return { ...previous, [currentUser]: updated };
    });
  }

  function renderAccount(account) {
    return (
      <AccountRow
        account={account}
        isFollowing={followingByUser[currentUser].includes(account.username)}
        followsYou={followingByUser[account.username].includes(currentUser)}
        onToggleFollow={toggleFollow}
      />
    );
  }

  let searchMessage = '';
  if (searchedUsername === '') {
    searchMessage = 'Enter a username to search.';
  } else if (searchedUsername === currentUser) {
    searchMessage = 'You can’t follow your own account.';
  } else if (searchedUsername !== null && !match) {
    searchMessage = 'No account found with that username.';
  }

  return (
    <main className="friends-preview">
      <header>
        <p className="eyebrow">Boston Events</p>
        <h1>Friends</h1>
        <p className="muted">
          Try searching for the other mock account. Follows reset on refresh.
        </p>
      </header>

      <div className="preview-account">
        <label htmlFor="preview-user">Preview as</label>
        <select id="preview-user" value={currentUser} onChange={switchUser}>
          {accounts.map((account) => (
            <option key={account.username} value={account.username}>
              {account.displayName} (@{account.username})
            </option>
          ))}
        </select>
      </div>

      <section className="panel" aria-labelledby="search-title">
        <h2 id="search-title">Find people</h2>
        <form onSubmit={searchByUsername}>
          <label htmlFor="username">Username</label>
          <div className="search-controls">
            <input
              id="username"
              type="search"
              value={query}
              maxLength={50}
              placeholder={currentUser === 'jordan' ? 'taylor' : 'jordan'}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button type="submit">Search</button>
          </div>
        </form>
        <p className="muted search-message" role="status">{searchMessage}</p>
        {result && renderAccount(result)}
      </section>

      <div className="lists">
        <AccountList
          id="following-title"
          title="Following"
          entries={following}
          emptyMessage="You aren’t following anyone yet."
          renderAccount={renderAccount}
        />
        <AccountList
          id="followers-title"
          title="Followers"
          entries={followers}
          emptyMessage="You don’t have any followers yet."
          renderAccount={renderAccount}
        />
      </div>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<FriendsPreview />);
