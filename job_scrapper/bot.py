import discord
from discord.ext import tasks, commands
import os
import asyncio
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import scraper
from scraper import fetch_jobs
from yc_scraper import scrape_yc_jobs
from utils import database

import json

# --- CONFIGURATION ---
try:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'config.json')
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found.")
    exit(1)

DISCORD_TOKEN = config.get("discord_token")
CHANNEL_ID = int(config.get("channel_id", 0))

# Support both string (single) and list (multiple) for backward compatibility
SEARCH_TERMS = config.get("search_terms") or config.get("search_term")
if isinstance(SEARCH_TERMS, str):
    SEARCH_TERMS = [SEARCH_TERMS]

LOCATIONS = config.get("locations") or config.get("location")
if isinstance(LOCATIONS, str):
    LOCATIONS = [LOCATIONS]

SITES = config.get("sites", ["linkedin"])

SCRAPE_INTERVAL_HOURS = config.get("scrape_interval_hours", 6)

# Initialize Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    database.init_db()
    print("Database initialized.")
    if not job_scraper_task.is_running():
        job_scraper_task.start()

@tasks.loop(hours=SCRAPE_INTERVAL_HOURS)
async def job_scraper_task():
    print("Starting scheduled scrape...")
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print(f"Error: Channel with ID {CHANNEL_ID} not found. Please set a valid DISCORD_CHANNEL_ID.")
        return

    new_jobs_count = 0
    for location in LOCATIONS:
        for term in SEARCH_TERMS:
            print(f"Scraping for '{term}' in '{location}'...")
            # Exclude ycombinator from jobspy sites as it is handled separately
            jobspy_sites = [s for s in SITES if s != "ycombinator"]
            if jobspy_sites:
                jobs = fetch_jobs(search_term=term, location=location, jobs_to_fetch=10, site_name=jobspy_sites)
            else:
                jobs = []
            
            new_jobs_count_for_term = 0
            for job in jobs:
                # jobspy returns somewhat messy data sometimes, ensure we have keys
                job_id = job.get('id')
                
                if not job_id:
                    # Fallback if no ID, use title+company+url as unique enough hash
                    job_id = f"{job.get('title')}-{job.get('company')}"

                if not database.is_job_seen(job_id):
                    database.add_job(job)
                    new_jobs_count_for_term += 1
                    new_jobs_count += 1
                    
                    # Create Embed
                    embed = discord.Embed(
                        title=job.get('title', 'Unknown Title'),
                        url=job.get('job_url', ''),
                        description=f"**Company:** {job.get('company', 'Unknown')}\n**Location:** {job.get('location', 'Unknown')}",
                        color=0x00ff00
                    )
                    if job.get('salary_source'):
                         embed.add_field(name="Salary", value=f"{job.get('min_amount')}-{job.get('max_amount')} {job.get('currency')}", inline=False)
                    
                    site_source = job.get('site', 'Unknown Source').capitalize()
                    embed.set_footer(text=f"Source - {site_source}")

                    try:
                        await channel.send(embed=embed)
                        await asyncio.sleep(1) # Rate limit protection for Discord
                    except Exception as e:
                        print(f"Failed to send message: {e}")
            
            print(f"Finished scraping '{term}' in '{location}'. Found {new_jobs_count_for_term} new jobs.")
            await asyncio.sleep(5) # Polite delay between different search terms

    # --- YCombinator Scraper Integration ---
    if "ycombinator" in SITES:
        # Map generic terms to YC roles or just scrape default "software-engineer"
        # For this implementation, we'll check if any search term implies engineering/product/design
        # and scrape the corresponding YC role.
        
        yc_roles = set()
        for term in SEARCH_TERMS:
            term_lower = term.lower()
            if "manager" in term_lower or "product" in term_lower:
                yc_roles.add("product-manager")
            elif "design" in term_lower or "ui" in term_lower or "ux" in term_lower:
                yc_roles.add("designer")
            elif "sales" in term_lower:
                yc_roles.add("sales-manager")
            elif "hr" in term_lower or "recruiting" in term_lower:
                yc_roles.add("recruiting-hr")
            else:
                # Default to software engineer for most technical terms
                yc_roles.add("software-engineer")
        
        for role in yc_roles:
            print(f"Scraping YCombinator for role '{role}'...")
            yc_jobs = scrape_yc_jobs(role=role)
            new_yc_jobs_count = 0
            
            for job in yc_jobs:
                 if not database.is_job_seen(job['id']):
                    database.add_job(job)
                    new_yc_jobs_count += 1
                    new_jobs_count += 1
                    
                    # Create Embed
                    embed = discord.Embed(
                        title=job.get('title', 'Unknown Title'),
                        url=job.get('job_url', ''),
                        description=f"**Company:** {job.get('company', 'Unknown')}\n**Location:** {job.get('location', 'Unknown')}",
                        color=0xff7f00 # Orange for YC
                    )
                    if job.get('salary_source'):
                         embed.add_field(name="Salary", value=job.get('salary_source'), inline=False)
                    
                    embed.set_footer(text=f"Source - YCombinator")

                    try:
                        await channel.send(embed=embed)
                        await asyncio.sleep(1)
                    except Exception as e:
                        print(f"Failed to send message: {e}")
            
            print(f"Finished scraping YCombinator '{role}'. Found {new_yc_jobs_count} new jobs.")
            await asyncio.sleep(5)

    print(f"Total job scrape finished. Posted {new_jobs_count} total new jobs across all categories.")

@job_scraper_task.before_loop
async def before_job_scraper_task():
    await bot.wait_until_ready()

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set.")
    else:
        bot.run(DISCORD_TOKEN)
