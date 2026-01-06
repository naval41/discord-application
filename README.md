# Interview Networker Discord Bots

This repository contains a suite of Discord bots designed to help users network and prepare for interviews.

1.  **Job Scraper Bot**: Fetches job listings from LinkedIn, YCombinator, and other sites.
2.  **LeetCode Interview Scraper**: Scrapes interview experiences from LeetCode, extracts insights using AWS Bedrock, and posts them to Discord.

## Directory Structure

-   `job_scrapper/`: Logic for the Job Scraper bot (`bot.py`).
-   `lc_interview_experience_scrapper/`: Logic for the LeetCode Scraper (`main.py`, `lc_client.py`).
-   `utils/`: Shared resources, configuration, and database logic (`config.json`, `bedrock_service.py`, `postgres_db.py`).
-   `Database_Schema.sql`: SQL schema for the PostgreSQL database.

## Prerequisites

-   **Python 3.10+** (Required for `python-jobspy` and modern asyncio)
-   **PostgreSQL**: Local or hosted instance.
-   **AWS Credentials**: Access to AWS Bedrock (Claude 3.5 Sonnet).

## Database Setup

1.  Ensure PostgreSQL is running.
2.  Create a database named `postgres` (or as configured).
3.  Run the schema script to create tables:
    ```bash
    psql -U postgres -d postgres -f Database_Schema.sql
    ```

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Edit `utils/config.json` to set your credentials and preferences.

```json
{
    "discord_token": "YOUR_DISCORD_BOT_TOKEN",
    "channel_id": 123456789012345678,
    "search_terms": ["Software Engineer"],
    "locations": ["Remote", "USA"],
    "sites": ["linkedin", "ycombinator"],
    "scrape_interval_hours": 6,
    "lc_scrape_interval_hours": 6,
    "postgres": {
        "host": "localhost",
        "port": 5432,
        "database": "postgres",
        "user": "postgres",
        "password": "your_password",
        "schema": "public"
    },
    "bedrock": {
        "region": "us-east-1",
        "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "aws_access_key_id": "YOUR_AWS_ACCESS_KEY",
        "aws_secret_access_key": "YOUR_AWS_SECRET_KEY"
    }
}
```

## Running the Bots

You can run each bot in a separate terminal or as a background process.

### 1. Job Scraper Bot
This bot scrapes job boards and posts new listings to Discord.

```bash
python3 job_scrapper/bot.py
```

### 2. LeetCode Interview Scraper
This bot scrapes interview experiences, processes them with AI, saves them to the DB, and posts a summary to Discord.

```bash
python3 lc_interview_experience_scrapper/main.py
```

### Background Execution (nohup)

To keep bots running after disconnecting:

```bash
# Job Scraper
nohup python3.11 job_scrapper/bot.py > job_bot.log 2>&1 &

# LeetCode Scraper
nohup python3.11 lc_interview_experience_scrapper/main.py > lc_bot.log 2>&1 &
```

**Manage processes:**
-   Check running: `ps aux | grep python3`
-   Stop: `kill <PID>`


## Production Setup

1.  PIP Installation 
```
python3.11 -m pip install -r requirements.txt

```