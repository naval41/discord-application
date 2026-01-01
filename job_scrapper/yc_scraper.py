import requests
from bs4 import BeautifulSoup
import datetime

def scrape_yc_jobs(role="software-engineer", location=None):
    """
    Scrapes jobs from YCombinator based on role.
    Note: 'location' is not directly used in the URL filter here as YC URL structure is role-based,
    but we can filter results after scraping if strict location is needed.
    """
    url = f"https://www.ycombinator.com/jobs/role/{role}"
    print(f"Scraping YC jobs from {url}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Matches the 'li' container class observed
        job_cards = soup.find_all('li', class_="my-2 flex h-auto w-full flex-col flex-nowrap rounded border border-[#ccc] bg-beige-lighter px-5 py-3")
        
        jobs = []
        for card in job_cards:
            try:
                # Title and Link
                title_elem = card.select_one('a.text-linkColor')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                job_url = "https://www.ycombinator.com" + title_elem['href']
                
                # Company
                # Company name is usually in a bold span
                company_elem = card.select_one('span.font-bold')
                company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
                
                # Details (Location, Salary)
                # These are often in a flex container with bullets
                details_container = card.select_one('.flex.flex-wrap.items-center.gap-x-1')
                
                salary = "N/A"
                location_text = "Remote" # Default
                
                if details_container:
                    # Salary often contains '$' or '₹' or '€' or '£'
                    details_text = [div.get_text(strip=True) for div in details_container.find_all('div', recursive=False)]
                    
                    for item in details_text:
                        if any(currency in item for currency in ['$', '₹', '€', '£', 'K']):
                            salary = item
                        elif item not in ['•', 'Full-time', 'Contract', 'Engineering', 'Product', 'Design']:
                            # Heuristic for location: usually the longest remaining string or last item
                            # But simple heuristic: it's likely the one that's not the others.
                            # The last item is usually location in YC structure based on inspection
                            location_text = item

                # Parsing Salary for min/max if possible (simple split)
                min_amount = 0
                max_amount = 0
                currency = "USD"
                
                # Job ID from URL
                # e.g. /companies/peakflo/jobs/StcNZf7-data-analyst-remote-india -> StcNZf7
                job_img_id = job_url.split('/jobs/')[-1]
                
                job_dict = {
                    'id': f"yc-{job_img_id}", # Prefix to avoid collision
                    'title': title,
                    'company': company,
                    'job_url': job_url,
                    'location': location_text,
                    'site': 'ycombinator',
                    'min_amount': min_amount, # Placeholder, robust parsing is complex
                    'max_amount': max_amount,
                    'currency': currency,
                    'salary_source': salary if salary != "N/A" else None,
                    'date_posted': datetime.date.today().isoformat()
                }
                
                jobs.append(job_dict)
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
                
        print(f"Found {len(jobs)} YC jobs.")
        return jobs

    except Exception as e:
        print(f"Error fetching YC jobs: {e}")
        return []

if __name__ == "__main__":
    # Test run
    results = scrape_yc_jobs()
    print(f"First result: {results[0] if results else 'No results'}")
