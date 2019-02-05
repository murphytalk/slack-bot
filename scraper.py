#!/usr/bin/env python3
import sys
from dataclasses import dataclass
from threading import Thread
from queue import PriorityQueue
from scrapy.spiders import CrawlSpider, Rule
from scrapy import Field, Item
from scrapy.linkextractors import LinkExtractor as E
from scrapy.crawler import CrawlerProcess, Crawler
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
from urllib.parse import urlparse
from typing import Tuple
from multiprocessing import Process, Queue
from scrapy import signals

taskQ = PriorityQueue()


@dataclass
class MyRule:
    xpath: str
    rules: Tuple[Rule]
    domain: str = ''
    url: str = ''


rules = {
    'www.khanacademy.org': MyRule(
        "//div[contains(@class,'container_1o7qpn5')]/text()",
        (Rule(E(allow=('[a-z\-]')),callback='parse_item'),)
    )
}


class MyItem(Item):
    text = Field()


class MySpider(CrawlSpider):
    """
    use scrapy view http://..... to see page before being modified by JavaScript
    """

    custom_settings = {
        'USER_AGENT': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    }

    def __init__(self, rule):
        self.xpath = rule.xpath

        self.rules = rule.rules
        self.start_urls = [rule.url]
        self.name = rule.domain
        self.allowed_domains = [rule.domain]
        super(MySpider, self).__init__()


    def parse_item(self, response):
        txt = response.xpath(self.xpath).getall()
        item = MyItem()
        item['text'] = txt[0] if txt and len(txt) >= 1 else None
        print(item['text'])
        return item


configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})


class CustomCrawler(object):
    def crawl(self, spider,rule):
        crawled_items = []

        def add_item(item):
            crawled_items.append(item)

        process = CrawlerProcess()

        crawler = Crawler(spider)
        crawler.signals.connect(add_item, signals.item_scraped)
        process.crawl(crawler, rule)

        process.start()

        return crawled_items


def crawl(url):
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
        p = Process(target=_crawl, args=(q,r))
        p.start()
        res = q.get()
        p.join()
        return res

    return None

if __name__ == "__main__":
    for url in sys.argv[1:]:
        print(crawl(url))
