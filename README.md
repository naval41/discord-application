# Job Scraper Discord Bot

A Discord bot that scrapes job listings from LinkedIn, YCombinator, and other sites, stores them in a local database to avoid duplicates, and posts new findinds to a Discord channel.

## Directory Structure
- `job_scrapper/`: Contains the bot logic (`bot.py`) and scrapers (`scraper.py`, `yc_scraper.py`).
- `utils/`: Contains shared resources (`config.json`, `database.py`, `jobs.db`).

## Prerequisites
- **Python 3.10+** (Required for `python-jobspy`)
- `pip`

## Installation

1. Clone the repository or copy files to your server.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you are on a restricted server and need to update Python, refer to your OS documentation or use Pyenv.*

## Configuration

Edit `utils/config.json` to set your preferences:

```json
{
    "discord_token": "YOUR_DISCORD_BOT_TOKEN",
    "channel_id": 123456789012345678,
    "search_terms": ["Python Developer", "Software Engineer"],
    "locations": ["Remote", "USA"],
    "sites": ["linkedin", "ycombinator"],
    "scrape_interval_hours": 6
}
```

## Running the Bot

### 1. Local / Interactive Mode
To run the bot and see logs in your terminal:
```bash
python3 job_scrapper/bot.py
```

### 2. server / Background Mode (EC2)
To keep the bot running after you disconnect from your SSH session, use `nohup`:

**Start the bot:**
```bash
nohup python3 job_scrapper/bot.py > bot.log 2>&1 &
```

**Manage the process:**
- **Check if running:** `ps aux | grep bot.py`
- **View logs:** `tail -f bot.log`
- **Stop the bot:** 
  1. Find the PID from the `ps` command.
  2. Run `kill <PID>`.
