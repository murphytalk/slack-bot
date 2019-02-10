#!/usr/bin/env python3
import sys
from dataclasses import dataclass
from scrapy import signals
from scrapy.spiders import Spider
from scrapy import Field, Item
from scrapy.settings import Settings
from scrapy.crawler import CrawlerProcess, Crawler
from scrapy.utils.log import configure_logging
from urllib.parse import urlparse
from multiprocessing import Process, Queue


@dataclass
class MyRule:
    xpath: str
    domain: str = ''
    url: str = ''


rules = {
    'www.khanacademy.org': MyRule("//div[contains(@class,'container_1o7qpn5')]/text()")
}

custom_settings = {
    'USER_AGENT': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
}


class MyItem(Item):
    text = Field()


class MySpider(Spider):
    """
    use scrapy view http://..... to see page before being modified by JavaScript
    """
    def __init__(self, rule):
        self.xpath = rule.xpath

        self.start_urls = [rule.url]
        self.name = rule.domain
        super(MySpider, self).__init__()

    def parse(self, response):
        txt = response.xpath(self.xpath).getall()
        item = MyItem()
        item['text'] = txt[0] if txt and len(txt) >= 1 else None
        return item


configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})


class CustomCrawler(object):
    def crawl(self, spider, rule):
        crawled_items = []

        def add_item(item):
            crawled_items.append(item)

        s = Settings(custom_settings)
        process = CrawlerProcess(s)
        crawler = Crawler(spider, s)
        crawler.signals.connect(add_item, signals.item_scraped)
        process.crawl(crawler, rule)

        process.start()

        return crawled_items


class Scraper(object):
    @staticmethod
    def run(url):
        """
        url is already santinized by caller
        """
        def _crawl(queue, rule):
            crawler = CustomCrawler()
            res = crawler.crawl(MySpider, rule)
            queue.put(res)

        uri = urlparse(url)
        uri = uri.netloc if uri.netloc else None
        if uri in rules:
            r = rules[uri]
            r.url = url
            r.domain = uri
            q = Queue()
            p = Process(target=_crawl, args=(q, r))
            p.start()
            res = q.get()
            p.join()
            return res

        return None


if __name__ == "__main__":
    for url in sys.argv[1:]:
        print(Scraper.run(url))
