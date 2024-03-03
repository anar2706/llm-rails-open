from bs4 import BeautifulSoup as bs, Comment

class WebsiteCrawler:
    def __init__(self, link, store_id, user):
        self.host = None
        self.user = user
        self.store_id = store_id
        self.link = link
        
    @staticmethod
    def tag_visible(element):
        if element.parent.name in [
            "style",
            "script",
            "head",
            "title",
            "meta",
            "[document]",
        ]:
            return False
        return not isinstance(element, Comment)

    def get_webpage_data(self, url, content): 
        soup = bs(content, "html.parser")
        texts = soup.findAll(string=True)
        visible_texts = filter(self.tag_visible, texts)
        return " ".join(t.strip() for t in visible_texts)

    def scrape_links(self):
        payload = {"url": self.link['url'], "text": self.get_webpage_data(self.link['url'],self.link['data'])}
        return [payload]

    def crawl(self):
        return self.scrape_links()
