import urllib
from fastapi import HTTPException
import requests
from bs4 import BeautifulSoup as bs


class WebsiteLinksCrawler:
    def __init__(self, url):
        self.host = None
        self.url = url
        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-language": "en-US,en;q=0.9,az;q=0.8,ru;q=0.7,tr;q=0.6,la;q=0.5",
            "dnt": "1",
            "sec-ch-ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "sec-gpc": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        }

    def get_all_links(self, soup):
        links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            if href and (href.startswith("/") or href.startswith(self.host)):
                links.append(href)
        return links

    def scrape_recursively(self, url):
        visited_urls = set()
        self.host = f"{urllib.parse.urlsplit(url).scheme}://{urllib.parse.urlsplit(url).hostname}"
        self._scrape_recursively_helper(url, visited_urls)

        return visited_urls

    def _scrape_recursively_helper(self, url, visited_urls):
        if url in visited_urls:
            return
        
        if url[:-1] in visited_urls:
            return
        
        visited_urls.add(url)
        print("Scraping:", url)
        
        try:
            response = requests.get(url, headers=self.headers, allow_redirects=True,timeout=5)
            soup = bs(response.text, "html.parser")
            all_links = self.get_all_links(soup)

            for link in all_links:
                if link.startswith("/"):
                    link = self.host + link
                if len(visited_urls) > 30:
                    return visited_urls
                self._scrape_recursively_helper(link, visited_urls)
        
        except Exception as e:
            print(f'e {e}')
            pass

    def crawl(self):
        return self.scrape_recursively(self.url)
