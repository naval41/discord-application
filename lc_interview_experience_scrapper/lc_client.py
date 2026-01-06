import tls_client
import json
import time
from bs4 import BeautifulSoup

class LeetCodeClient:
    URL = "https://leetcode.com/graphql/"
    
    def __init__(self):
        # Use Chrome 120 identifier to mimic a real browser and bypass Cloudflare
        self.session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        # Minimal headers to prevent fingerprinting mismatches
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })

    def fetch_discussion_posts(self, limit=50, skip=0):
        query = """
        query discussPostItems($orderBy: ArticleOrderByEnum, $keywords: [String]!, $tagSlugs: [String!], $skip: Int, $first: Int) {
            ugcArticleDiscussionArticles(
                orderBy: $orderBy
                keywords: $keywords
                tagSlugs: $tagSlugs
                skip: $skip
                first: $first
            ) {
                totalNum
                pageInfo {
                    hasNextPage
                }
                edges {
                    node {
                        uuid
                        title
                        slug
                        summary
                        topicId
                        author {
                            realName
                            userAvatar
                        }
                        tags {
                            name
                            slug
                        }
                        creationDate: createdAt
                        content
                    }
                }
            }
        }
        """
        
        variables = {
            "orderBy": "HOT",
            "keywords": [""],
            "tagSlugs": ["interview"],
            "skip": skip,
            "first": limit
        }
        
        payload = {
            "query": query,
            "variables": variables,
            "operationName": "discussPostItems"
        }
        
        try:
            # For GraphQL, we need minimal headers too, but Content-Type is needed
            headers = {
                "Content-Type": "application/json",
                "User-Agent": self.session.headers["User-Agent"]
            }
            
            response = self.session.post(self.URL, json=payload, headers=headers)
            
            if response.status_code != 200:
                print(f"Error fetching LeetCode posts: Status {response.status_code}")
                return None
                
            try:
                return response.json()
            except json.JSONDecodeError:
                print(f"Error decoding JSON. Response content preview:\n{response.text[:500]}...")
                return None
        except Exception as e:
            print(f"Error fetching LeetCode posts: {e}")
            return None

    def fetch_post_content(self, url):
        # List of profiles to try in case of 403
        profiles = ["chrome_120", "firefox_120", "safari_16_0", "opera_90"]
        
        for profile in profiles:
            try:
                time.sleep(2) # Politeness delay
                
                # Create a temporary session for this request to try specific profile
                temp_session = tls_client.Session(
                    client_identifier=profile,
                    random_tls_extension_order=True
                )
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://leetcode.com/discuss/interview-experience?currentPage=1&orderBy=hot&query=",
                }
                
                if "safari" in profile:
                     headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15"

                response = temp_session.get(url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content_div = soup.find('div', class_="relative mt-4 flex w-full flex-none flex-col overflow-auto px-4 pb-8 gap-4")
                    
                    if content_div:
                        return content_div.get_text(separator="\n", strip=True)
                    else:
                        print(f"Warning: Content div not found for {url}")
                        return ""
                elif response.status_code == 403:
                    print(f"  - 403 Forbidden with {profile}. Retrying with next profile...")
                    continue
                else:
                    print(f"Error scraping post content from {url}: Status {response.status_code}")
                    return ""

            except Exception as e:
                print(f"Error scraping post content from {url} with {profile}: {e}")
                continue
        
        print(f"Failed to scrape {url} after trying all profiles.")
        return ""
