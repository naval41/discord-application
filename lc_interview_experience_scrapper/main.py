import sys
import os
import time
import json
from datetime import datetime

# Add parent directory to path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.database import setup_leetcode_tracking, is_leetcode_post_visited, mark_leetcode_post_visited
from utils.postgres_db import PostgresDB
from lc_client import LeetCodeClient
from bedrock_client import BedrockProcessor
from utils.discord_service import DiscordSender

# --- CONFIGURATION ---
try:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'config.json')
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found.")
    exit(1)

SCRAPE_INTERVAL_HOURS = config.get("lc_scrape_interval_hours", 6)

def run_scraper():
    print(f"[{datetime.now()}] Starting LeetCode Interview Scraper (v2 - Multi-Step)...")
    
    # 1. Initialize
    setup_leetcode_tracking()
    pg_db = PostgresDB()
    lc_client = LeetCodeClient()
    bedrock = BedrockProcessor()
    
    processed_count = 0
    skipped_count = 0
    
    # Loop for 5 pages
    for page in range(5):
        skip = page * 50
        print(f"\n--- Processing Page {page + 1} (Skip: {skip}) ---")
        
        # 2. Fetch Posts
        print("Fetching posts from LeetCode...")
        data = lc_client.fetch_discussion_posts(limit=50, skip=skip)
        
        if not data or "data" not in data:
            print("Failed to fetch data or end of pages.")
            break

        posts = data["data"]["ugcArticleDiscussionArticles"]["edges"]
        if not posts:
            print("No posts found. Stopping.")
            break
            
        print(f"Found {len(posts)} posts. Processing...")
        
        for edge in posts:
            node = edge["node"]
            uuid = node["uuid"]
            title = node["title"]
            summary = node["summary"]
            topic_id = node["topicId"]
            
            # 3. Check Visited
            if is_leetcode_post_visited(uuid):
                print(f"Skipping {uuid} (Already visited)")
                skipped_count += 1
                continue
                
            print(f"Processing {uuid}: {title} : {topic_id}")
            
            # 3.5 Fetch Full Content
            post_url = f"https://leetcode.com/discuss/post/{topic_id}/"
            full_content = lc_client.fetch_post_content(post_url)
            
            content_to_use = full_content if full_content else summary
            if full_content:
                print(f"  - Scraped full content url : {post_url} ({len(full_content)} chars)")
            else:
                print(f"  - Failed to scrape content, using summary ({len(summary)} chars)")

            # 4. Step 1: Check Interview & Extract Company
            company_info = bedrock.extract_company_info(title, content_to_use)
            
            if not company_info or not company_info.get("is_interview_experience"):
                print(f"  - Not an interview experience (or failed extraction).")
                mark_leetcode_post_visited(uuid)
                continue
                
            company_name = company_info.get("company_name")
            if not company_name:
                print("  - Interview experience, but no company name found.")
                mark_leetcode_post_visited(uuid)
                continue
                
            # 5. Step 2: Get/Create Company in DB
            company_slug = company_name.lower().replace(" ", "-")
            company = pg_db.get_or_create_company(company_name, company_slug)
            print(f"  - Company: {company['name']} ({company['id']})")
            
            # 6. Step 3: Fetch Internal Job Roles
            job_roles = pg_db.get_job_roles_for_company(company['id'])
            
            # 7. Step 4: Extract Interview Details with Context
            extraction = bedrock.extract_interview_details(title, content_to_use, job_roles)
            if not extraction:
                print("  - Failed to extract detailed interview info.")
                # Don't mark visited? Or mark visited? 
                # If step 1 passed but step 4 failed, it's an error. 
                # Let's NOT mark visited so we can retry if it's transient.
                continue
                
            try:
                # Resolve Job Role ID
                job_role_id = extraction.get("job_role_id")
                
                # Validation: Check if returned ID is valid for this company
                valid_ids = [r['id'] for r in job_roles]
                if job_role_id not in valid_ids:
                    print(f"  - Bedrock returned invalid/unknown Job Role ID: {job_role_id}. Falling back.")
                    # Fallback strategies: 
                    # 1. Try to find "Software Engineer" in the list
                    # 2. Pick the first one?
                    # 3. Use a global default?
                    # For now, let's try to match by name "Software Engineer" or skip.
                    
                    fallback_role = next((r for r in job_roles if "software engineer" in r['name'].lower()), None)
                    if fallback_role:
                        job_role_id = fallback_role['id']
                        print(f"  - Fallback to: {fallback_role['name']}")
                    elif job_roles:
                        job_role_id = job_roles[0]['id'] # Desperate fallback
                        print(f"  - Desperate fallback to first role: {job_roles[0]['name']}")
                    else:
                        # No roles at all for this company? 
                        # We might need to create a default role for the company? 
                        # Or search global "Software Engineer"?
                        # Based on user logic: "Query internal Postgres... Go to Job Profile and Job Role..."
                        # If empty, maybe search global?
                        global_role = pg_db.get_job_role_by_name("Software Engineer")
                        if global_role:
                            job_role_id = global_role['id']
                            print("  - Fallback to GLOBAL Software Engineer role.")
                        else:
                            print("  - CRITICAL: No Job Role found. Skipping.")
                            mark_leetcode_post_visited(uuid) 
                            continue

                # Create Interview
                try:
                    num_rounds = int(extraction.get("number_of_rounds", 0))
                except (ValueError, TypeError):
                    num_rounds = 0

                try:
                    rating = float(extraction.get("overall_rating", 0))
                except (ValueError, TypeError):
                    rating = 0.0

                interview_data = {
                    "companyId": company['id'],
                    "userId": "1",
                    "jobRoleId": job_role_id,
                    "slug": node['slug'],
                    "title": title,
                    "location": extraction.get("location"),
                    "date": datetime.now(),
                    "difficulty": extraction.get("interview_difficulty", "Medium").upper(),
                    "noOfRounds": num_rounds,
                    "interviewProcess": extraction.get("company_interview_process"),
                    "preparationSources": extraction.get("preparation_source"),
                    "overallRating": rating,
                    "isAnonymous": extraction.get("is_anonymous", False),
                    "status": "PUBLISHED",
                    "offerStatus": extraction.get("offer_status", "PENDING").upper()
                }
                
                # ENUM validations
                valid_difficulties = ["EASY", "MEDIUM", "HARD"]
                if interview_data["difficulty"] not in valid_difficulties:
                     interview_data["difficulty"] = "MEDIUM"

                # Mapping
                status_map = {
                    "Offer": "OFFERED", 
                    "Pending": "PENDING", 
                    "Rejected": "REJECTED",
                    "Accepted": "OFFERED",
                    "Declined": "REJECTED"
                }
                mapped_status = status_map.get(extraction.get("offer_status"), "PENDING")
                
                valid_offer_status = ["OFFERED", "PENDING", "REJECTED"]
                if mapped_status not in valid_offer_status: mapped_status = "PENDING"
                
                interview_data["offerStatus"] = mapped_status

                interview_id = pg_db.create_interview(interview_data)
                print(f"  - Created Interview: {interview_id}")
                
                # Rounds
                print(f"  - Processing {len(extraction.get('interview_rounds', []))} rounds...")
                for round_data in extraction.get("interview_rounds", []):
                    r_diff = round_data.get("difficulty", "Medium").upper()
                    if r_diff not in valid_difficulties: r_diff = "MEDIUM"
                    
                    start_index = 1
                    try:
                        start_index = int(round_data.get("sequence", 1))
                    except:
                        pass

                    round_db_data = {
                        "interviewId": interview_id,
                        "name": round_data.get("name", f"Round {start_index}"),
                        "duration": round_data.get("duration"),
                        "difficulty": r_diff,
                        "experience": round_data.get("experience", ""),
                        "keyTakeaways": round_data.get("key_takeaways"),
                        "orderIndex": start_index
                    }
                    pg_db.create_interview_round(round_db_data)

                # Send Discord Notification
                try:
                    discord = DiscordSender()
                    
                    # Resolve Job Role Name and Profile Name
                    role_name = "Software Engineer"
                    profile_name = "Software Engineering" # Default fallback
                    if job_roles:
                         matched_role = next((r for r in job_roles if r['id'] == job_role_id), None)
                         if matched_role:
                             role_name = matched_role['name']
                             profile_name = matched_role.get('profile_name', 'Software Engineering')

                    # Status Colors
                    color_map = {
                        "OFFERED": 0x43B581, # Green
                        "PENDING": 0xFFAA00, # Orange
                        "REJECTED": 0xF04747  # Red
                    }
                    embed_color = color_map.get(interview_data['offerStatus'], 0x3498DB) # Default Blue

                    # Build Description from Rounds
                    description = ""
                    for i, r_data in enumerate(extraction.get("interview_rounds", [])):
                        r_name = r_data.get("name", f"Round {i+1}")
                        r_exp = r_data.get("experience", "")
                        # Truncate experience for preview
                        preview = (r_exp[:150] + '...') if len(r_exp) > 150 else r_exp
                        # Add emoji based on name keywords
                        emoji = "🔘"
                        if "coding" in r_name.lower() or "dsa" in r_name.lower(): emoji = "💻"
                        elif "system" in r_name.lower() and "design" in r_name.lower(): emoji = "🏗️"
                        elif "behavioral" in r_name.lower() or "manager" in r_name.lower(): emoji = "💬"
                        
                        description += f"{emoji} **{r_name}**\n{preview}\n\n"

                    # Quality Check: Skip if description is empty or contains <UNKNOWN>
                    if not description.strip() or "<UNKNOWN>" in description:
                        print(f"  - Discord notification skipped (Low quality/Unknown content).")
                    else:
                        # Construct Embed
                        link = f"https://roundz.ai/interviews/{interview_id}/{interview_data['slug']}"
                        
                        # Formatted Title: Company | Job Profile | Job Role | Location (if present) | Offer Status
                        loc_raw = interview_data.get('location')
                        loc_str = str(loc_raw).strip() if loc_raw else ""
                        invalid_locs = ["", "none", "unknown", "null", "<unknown>"]
                        is_valid_loc = loc_str and loc_str.lower() not in invalid_locs
                        loc_part = f" | {loc_str}" if is_valid_loc else ""
                        formatted_title = f"{company['name']} | {profile_name} | {role_name}{loc_part} | {interview_data['offerStatus']}"
                        
                        embed = {
                            "title": formatted_title,
                            "url": link,
                            "color": embed_color,
                            "fields": [
                                {"name": "Company", "value": company['name'], "inline": True},
                                {"name": "Role", "value": role_name, "inline": True},
                                {"name": "Difficulty", "value": interview_data['difficulty'], "inline": True},
                                {"name": "Status", "value": interview_data['offerStatus'], "inline": True},
                                {"name": "Rounds", "value": str(num_rounds), "inline": True},
                                {"name": "Location", "value": loc_str if is_valid_loc else "Unspecified", "inline": True}
                            ],
                            "description": description,
                            "footer": {
                                "text": f"Roundz AI | Interview Experiences | {datetime.now().strftime('%m/%d/%Y')}"
                            }
                        }
                        
                        discord.send_message("1455048561275306074", content=None, embed=embed)
                        print(f"  - Discord notification sent.")
                except Exception as dx:
                    print(f"  - Failed to send Discord notification: {dx}")
                    pass
                    
                processed_count += 1
                mark_leetcode_post_visited(uuid)
                
            except Exception as e:
                print(f"  - Error saving to DB: {e}")
                pass

    print(f"\nTotal Done. Processed: {processed_count}, Skipped: {skipped_count}")

def main():
    print(f"Starting Scheduled Scraper (Interval: {SCRAPE_INTERVAL_HOURS} hours)")
    while True:
        try:
            run_scraper()
        except Exception as e:
            print(f"Critical Error in regular run: {e}")
        
        print(f"Run complete. Sleeping for {SCRAPE_INTERVAL_HOURS} hours...")
        time.sleep(SCRAPE_INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    main()
