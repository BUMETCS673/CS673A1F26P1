# Simple user database

A standalone PostgreSQL database with one `users` table and two fictional users.
The Python API connects to it through the shared `cs673_event_planning` Docker
network. React's development server can forward requests to that API. There is
The API's register/login endpoints store accounts here with hashed passwords, and
login sessions in a `user_sessions` table. The two sample users have no password,
so they cannot log in. `start_project.sh` applies `migrations/*.sql` on every start.

To run all three project parts together, follow
[HOW_TO_START_AND_STOP_PROJECT.md](../HOW_TO_START_AND_STOP_PROJECT.md).
Its stop script deliberately deletes this database's local data. The commands
below explain how to work with the database on its own.

## First-time setup

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   and start it. It includes Docker Compose. On Linux, Docker Engine with the
   Compose plugin also works.
2. If using Windows with WSL, enable integration for your WSL distribution in
   Docker Desktop under **Settings > Resources > WSL Integration**.
3. Clone this GitHub repository (or pull the branch containing this folder).
   Open a terminal in the repository's `code` folder and run:

```bash
cd User_Database
docker compose up -d --wait
```

That is the whole database setup. Docker downloads PostgreSQL, starts it in the
background, and creates the table and sample users automatically. The first run
needs internet access to download the image. No separate PostgreSQL installation,
Python packages, npm packages, or configuration files are needed.

After setup, open the database's SQL terminal:

```bash
docker compose exec database psql -U movie_admin -d movie_users
```

Run this SQL to see the two sample rows (include the semicolon):

```sql
SELECT * FROM users ORDER BY id;
```

Type `\q` and press Enter to leave the SQL terminal. All `docker compose`
commands in this README run in your regular terminal, from `User_Database`.
All SQL examples run inside `psql`.

## Files and columns

- `docker-compose.yml`: describes how Docker starts PostgreSQL and saves data.
- `init.sql`: creates the table and inserts the two placeholders on first setup.
- `README.md`: setup and editing notes.

| Column | Meaning |
| --- | --- |
| `id` | Unique integer assigned automatically by PostgreSQL. |
| `username` | Required text, up to 50 characters, with no exact duplicates. |
| `email` | Required text, up to 255 characters, with no exact duplicates. |

The table does not validate email formatting. Text uniqueness is case-sensitive.

## Add a user

Open `psql` using the command above, then run:

```sql
INSERT INTO users (username, email)
VALUES ('new_user', 'new_user@example.com');

SELECT * FROM users ORDER BY id;
```

Choose a different username and email for each user. Omit `id` because PostgreSQL
creates it. SQL text values use single quotes. These are database records, not
PostgreSQL connection accounts.

To change one user's email, select that user with `WHERE`:

```sql
UPDATE users
SET email = 'alex_updated@example.com'
WHERE username = 'sample_alex';
```

## Add a column

For example, add an optional favorite genre to your existing local database:

```sql
ALTER TABLE users ADD COLUMN favorite_genre VARCHAR(50);

UPDATE users
SET favorite_genre = 'Comedy'
WHERE username = 'sample_alex';

SELECT * FROM users ORDER BY id;
```

Existing users start with `NULL` (no value) in the new column. Run the `ALTER`
command once; running it again produces a "column already exists" error.

Also add `favorite_genre VARCHAR(50)` to the column list in `init.sql`, with
commas between the column definitions, so future fresh setups get the column.
Changing `init.sql` alone does **not** change an existing database. Share both
the updated file and the `ALTER TABLE` command with teammates who already have
data. As the project grows, save those change commands in numbered SQL files
so everyone can apply the same updates in order.

## Stop, restart, and troubleshoot

Stop the container and keep your data:

```bash
docker compose stop database
```

Start it again with the usual setup command:

```bash
docker compose up -d --wait
```

Check the container status or read startup messages:

```bash
docker compose ps
docker compose logs database
```

If `docker` is unavailable or cannot connect, start Docker Desktop and check WSL
integration if applicable. If `--wait` is unrecognized, update Docker Compose.
If port 5432 is already in use, change the port line in `docker-compose.yml`
to `"127.0.0.1:5433:5432"`. The `docker compose exec` command stays the same.

To deliberately erase all local database data and start from `init.sql` again:

```bash
docker compose down -v
docker compose up -d --wait
```

**The `-v` option deletes the saved volume and all users and changes in it.**
Use plain `docker compose down` when you want to keep your work.
If the frontend/backend are running, stop those Compose projects first before
`down`: they share this database project's network. `stop database` preserves the
network and supports testing API outage/recovery without deleting any data.

## Sharing through GitHub

Share this folder's three files through the normal Git branch and pull request
workflow. Teammates run the same setup commands to create their own database.
Each computer has its own data: GitHub shares the structure and starter rows,
not users added locally. Docker stores the data in a named volume outside the
repository, so database files do not need to be committed or ignored manually.

For a database client such as pgAdmin, the local connection settings are:

| Setting | Value |
| --- | --- |
| Host | `localhost` |
| Port | `5432` (or `5433` if changed above) |
| Database | `movie_users` |
| Username | `movie_admin` |
| Password | `local_dev_password` |

The shared password is only for this local development database. Use separate,
private credentials before any future deployment. The connection account is an
administrator used only for local development; a deployment needs a separate
limited account. `/api/health/database` checks `SELECT 1` without reading users.
## Account Fields Migration (FV-113)

This migration adds three fields to the existing `users` table:

- `display_name` — stores the user's display name.
- `password_hash` — reserved for storing hashed passwords in future registration work.
- `activity_preferences` — stores a list of activity preferences, with an empty array as the default.

### Apply the migration

First, start the project using Docker:

```bash
bash start_project.sh
```

Then, from the `code` folder, run:

```bash
docker compose --project-directory User_Database exec -T database psql -v ON_ERROR_STOP=1 -U movie_admin -d movie_users < User_Database/migrations/001_account_fields.sql
```

This updates an existing development database without deleting the original users. The migration can be run more than once because it uses `ADD COLUMN IF NOT EXISTS`.

### Verify the migration

```bash
docker compose --project-directory User_Database exec database psql -U movie_admin -d movie_users -c "SELECT id, username, email, display_name, password_hash, activity_preferences FROM users ORDER BY id;"
```

The two sample users should remain, with their original IDs. Their `display_name` and `password_hash` values remain NULL, and `activity_preferences` defaults to an empty array.

Registration and login now use these columns (see `AI_Movie_Chatbot/app/routes/auth.py`).
`002_user_sessions.sql` adds the `user_sessions` table. `start_project.sh` applies
every migration automatically on each start; running them by hand is also safe.
