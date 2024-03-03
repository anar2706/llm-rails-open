from application.utils.general import timefn
from application.crawler.parse import WebsiteCrawler
from application.utils.converter import text_to_docs
from application.utils.file_loader import S3FileLoader
from crawl_models import CrawlerTasks


def get_size(txt):
    return len(txt.encode('utf-8'))

class DataHandler:
    
    @staticmethod
    def load_file(file, model, user):
        text = S3FileLoader(file).load()
        file_docs = text_to_docs([doc.page_content for doc in text], 
            user, model, file['original_name'], 'file', file['datastore_id'] + '/' + file['name'])
            
        return file_docs
    
    @staticmethod
    def load_text(text, model, user, name, datastore_id, url):
        file_docs = text_to_docs([text], user, model, name, "text", datastore_id + '/' + url)
        return file_docs
        
    @staticmethod
    @timefn
    def load_website(task_id, store_id, user, model):
        docs = []
        
        record = CrawlerTasks.select(CrawlerTasks.url,CrawlerTasks.data).where(CrawlerTasks.id == task_id).dicts()[0]
        website_data = WebsiteCrawler(record,store_id,user).crawl()
        size = get_size(record['data'])
        
        for item in website_data:
            docs += text_to_docs([item['text']], user, model, item["url"],'website', item["url"])
            
        return docs, size
        