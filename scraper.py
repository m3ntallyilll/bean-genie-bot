import requests
from bs4 import BeautifulSoup

# Target website
url = "https://www.onbigo.live/"

def extract_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Filter out invalid links
        if href and not href.startswith('javascript'):
            links.add(href)
    return links

def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def scrape_links_from_url(url):
    page_content = scrape_page(url)
    if page_content:
        links = extract_links(page_content)
        results = {}
        for link in links:
            full_link = link if link.startswith("http") else f"https://www.onbigo.live{link}"
            content = scrape_page(full_link)
            if content:
                results[full_link] = content
        return results
    return {}

def main(target_url=url):
    results = scrape_links_from_url(target_url)
    print(f"Found {len(results)} pages scraped.")
    for url, content in results.items():
        print(f"URL: {url}")
        print(f"Content length: {len(content)} characters")
        print("-" * 40)

if __name__ == "__main__":
    main()
