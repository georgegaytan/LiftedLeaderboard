# Lifted Leaderboard Bot

A Discord wellness leaderboard bot that tracks wellness logs, awards XP, and shows leaderboards for competing amongst the server.

## Project Structure

```
LiftedLeaderboard/
├── main.py                         # Entry point: loads .env, initializes DB, starts bot
├── src/
│   ├── bot.py                      # Discord client bootstrapping and cog loading
│   ├── cogs/                       # Slash command cogs
│   │   ├── activity_records_cog.py # /record, /recent (activity logging and views)
│   │   ├── leaderboard_cog.py      # /leaderboard
│   │   ├── user_cog.py             # /register, /profile
│   │   └── admin_cog.py            # Admin entry commands (category/activity management)
│   ├── components/                 # Discord UI components (Views/Modals/Embeds)
│   │   ├── activity_records.py     # Recent records view, edit/delete modals
│   │   ├── admin.py                # Activity/category admin editor views
│   │   └── leaderboard.py          # Leaderboard embed helpers
│   ├── database/                   # Database bootstrap and migrations
│   │   ├── start_db.py             # Runs schema init + migrations at startup
│   │   ├── create_migration.py     # Creates timestamped DB/Data migration template
│   │   ├── db_manager.py           # Postgres-only DB manager (psycopg)
│   │   ├── postgres_bootstrap.py   # Postgres DDL, indexes, triggers/functions
│   │   └── migrations/             # Migration scripts (Python)
│   └── utils/
│       ├── logs.py                 # Logging setup
│       ├── constants.py            # Constants, ranks, messages
│       └── helper.py               # Small helpers (e.g., level_to_rank)
├── requirements.txt                # Python dependencies
└── README.md
```

## Commands

- **/register**
  - Registers the invoking user in `users` (idempotent; updates display name on conflict).
- **/profile [member]**
  - Shows level, rank, and total XP for you or the specified member.
- **/leaderboard [top]**
  - Top users by `total_xp` (default 10, max 50).
- **/record category activity [note] [date]**
  - Records an activity occurrence, awards XP via triggers.
  - Optional daily bonus applies for the first record of the day.
- **/recent [limit] [sort_by]**
  - Shows your recent records with edit/delete UI (occurred/created/updated sort).
- **Admin (from `admin_cog.py` and `components/admin.py`)**
  - Manage activities: add or edit name/xp/category/is_archived

## Requirements

- **Python**: 3.11+
- **PostgreSQL**: Managed instance (e.g., Neon or local). SSL recommended.
- **psycopg**: `psycopg[binary,pool]`

## Setup

### 1) Create and activate a virtual environment

- Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
```

- macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2) Environment variables (.env.local / .env.prod)

This project uses environment-specific files loaded by `src.utils.env.load_env()`:

- **Selection rules**
  - Use file from `ENV_FILE` if set (absolute or relative path).
  - Else use `.env.prod` if `ENV` or `PYTHON_ENV` is `production`/`prod`.
  - Else use `.env.local` (default for development).
  - If the selected file is missing, a root `.env` (if present) is used as a fallback.

- **Variables**
  - `DISCORD_TOKEN` – Bot token.
  - `GUILD_ID` – Optional guild to scope command sync during development.
  - `DATABASE_URL` – PostgreSQL connection string.

- **.env.local (example)**
```env
ENV=local
DISCORD_TOKEN=your-local-bot-token
GUILD_ID=123456789012345678
DATABASE_URL=postgresql://postgres:password@localhost:5432/your_db
```

- **.env.prod (example)**
```env
ENV=production
DISCORD_TOKEN=your-production-bot-token
GUILD_ID=987654321098765432
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

- **Notes**
  - OS environment vars take precedence over file values (unless `load_env(override=True)`).
  - Files should generally not be committed. Consider adding to `.gitignore`:
    - `.env`, `.env.*` (and keep a non-secret `.env.example` if desired).

### 3) Run Bot

The entrypoint `main.py` will initialize schema and run any new migrations, then start the bot.

```bash
python main.py
```

If you prefer module execution:
```bash
python -m src.bot
```

## Development

- Optional pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Tests

```bash
python -m pytest tests/
```

## License

[LICENSE](LICENSE)
