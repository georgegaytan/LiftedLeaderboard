## Lincoln Leaderboard Bot

Discord wellness leaderboard bot. Tracks daily wellness logs, awards XP with boosts, shows leaderboards, and runs scheduled jobs (weekly resets, weather boosts).

### Quickstart
- **Python**: 3.11+
- **Install**:
  ```bash
  python -m venv .venv && .venv\\Scripts\\pip install -U pip
  .venv\\Scripts\\pip install -r requirements.txt
  ```
- **Config**: create a `.env` with at least:
  ```
  DISCORD_TOKEN=your-bot-token
  GUILD_ID=1234567890
  WEATHER_API_KEY=optional
  ```
- **Run**:
  ```bash
  python -m src.bot
  ```

### License
See [LICENSE](LICENSE).
