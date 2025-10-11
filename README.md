# Lifted Leaderboard Bot

A Discord wellness leaderboard bot that tracks wellness logs, awards XP, and shows leaderboards for competing amongst the server.

## Project Structure

```
LiftedLeaderboard/
├── src/
│   ├── bot.py                 # Main script
│   ├── cogs/                  # Discord command modules
│   │   ├── *_cog.py           # ...
│   ├── models/                # Data models
│   │   ├── *.py               # ...
│   ├── database/              # Database setup & migrations
│   │   ├── schema.py          # Database schema creation
│   │   ├── setup.py           # Database initialization script
│   │   └── migrations/        # Future database migrations
│   │       └── README.md      # Migration guidelines
│   ├── services/              
│   │   ├── db_manager.py      # Runtime DB operations
│   │   ├── xp_manager.py      # XP management
│   │   └── scheduler.py       # Scheduled tasks
│   └── utils/                 
│       ├── constants.py       
│       ├── embeds.py          # Embeds formatted for Discord
│       └── views.py           # Views for User notifications/input
├── data/                      # DB File is stored here
├── tests/                     
├── main.py                    # Alternative entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Commands
TODO: Command docs

## Requirements

- **Python**: 3.11+

## Setup

### 1️⃣ Install Dependencies

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

Create a `.env` file in the root of the project:

```env
DISCORD_TOKEN=your-bot-token
GUILD_ID=1234567890
WEATHER_API_KEY=optional
```

### 3️⃣ Initialize the Database

The bot uses SQLite. SQLite isn't a server, it's a minimalist approach that operates off of a single DB file. 
That file is stored at `data/wellness.db`.

Before running the bot for the first time, create the database and tables:

```powershell
python src/database/setup.py
```

You should see output confirming the tables exist:

```
Database and tables created/verified.
Current tables in DB: ['users', 'logs']
```

This will create `data/wellness.db`.



### 4️⃣ Run the Bot

```bash
python -m src.bot
```

## Tests

```bash
python -m pytest tests/
```

## License

[LICENSE](LICENSE)
