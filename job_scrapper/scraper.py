from jobspy import scrape_jobs
import pandas as pd

def fetch_jobs(search_term="Software Engineer", location="San Francisco, CA", jobs_to_fetch=20, site_name=["linkedin"]):
    """
    Fetches jobs from specified sites using JobSpy.
    Returns a list of dictionaries.
    """
    print(f"Scraping jobs for: {search_term} in {location} on {site_name}...")
    
    try:
        jobs: pd.DataFrame = scrape_jobs(
            site_name=site_name,
            search_term=search_term,
            location=location,
            results_wanted=jobs_to_fetch,
            hours_old=24, # Only get recent jobs
            country_watchlist=["US", "Canada", "India"],
        )
        
        if jobs.empty:
            print("No jobs found.")
            return []

        # Convert DataFrame to a list of dictionaries
        job_list = jobs.to_dict(orient='records')
        print(f"Found {len(job_list)} jobs.")
        return job_list

    except Exception as e:
        print(f"Error scraping jobs: {e}")
        return []

if __name__ == "__main__":
    # Test run
    results = fetch_jobs()
    print(results[:2])
