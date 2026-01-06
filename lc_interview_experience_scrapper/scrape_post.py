import tls_client
from bs4 import BeautifulSoup
import sys

def scrape_leetcode_post(url):
    print(f"Scraping URL: {url}")
    
    # Use Chrome 120 identifier with minimal headers to bypass Cloudflare
    session = tls_client.Session(
        client_identifier="chrome_120",
        random_tls_extension_order=True
    )
    
    # Minimal headers prevent fingerprinting mismatches that trigger 403s
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    
    try:
        response = session.get(url, headers=headers)
        
        if response.status_code != 200:
             print(f"Error: Received status code {response.status_code}")
             return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Target the specific content div
        target_class = "relative mt-4 flex w-full flex-none flex-col overflow-auto px-4 pb-8 gap-4"
        content_div = soup.find('div', class_=target_class)
        
        if content_div:
            print("\n" + "="*40)
            print("SCRAPED CONTENT")
            print("="*40)
            print(content_div.get_text(separator="\n", strip=True))
            print("="*40 + "\n")
        else:
             print("Content div NOT FOUND. The page structure might have changed or content is hidden.")
             print(f"Page Title: {soup.title.string if soup.title else 'No Title'}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_url = "https://leetcode.com/discuss/post/7460178/"
    url = sys.argv[1] if len(sys.argv) > 1 else test_url
    scrape_leetcode_post(url)
