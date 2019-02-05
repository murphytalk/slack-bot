#!/usr/bin/env python3
import sys
from dataclasses import dataclass
from threading import Thread
from queue import PriorityQueue
from scrapy.spiders import CrawlSpider, Rule
from scrapy import Field, Item
from scrapy.linkextractors import LinkExtractor as E
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
from urllib.parse import urlparse
from typing import Tuple

q = PriorityQueue()


@dataclass
class MyRule:
    xpath: str
    rules: Tuple[Rule]
    domain: str = ''
    url: str = ''


rules = {
    'www.khanacademy.org': MyRule(
        "//div[contains(@class,'container_1o7qpn5')]/text()",
        (Rule(E(allow=('relating-addition-and-subtraction')),callback='parse_item'),)
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
runner = CrawlerRunner()


def dispatch_to_crawler(url):
    """
    url is already santinized by caller
    """
    uri = urlparse(url)
    uri = uri.netloc if uri.netloc else None
    if uri in rules:
        r = rules[uri]
        r.url = url
        r.domain = uri
        d = runner.crawl(MySpider, r)
        d.addBoth(lambda _: reactor.stop())
        d = runner.join()
        reactor.run(installSignalHandlers=False)


def worker():
    while True:
        item = q.get()
        # item is a (priority, url) tuple
        if item[1] is None:
            break
        dispatch_to_crawler(item[1])
        q.task_done()


def start():
    t = Thread(target=worker)
    t.start()
    return t


if __name__ == "__main__":
    for url in sys.argv[1:]:
        q.put((0, url))
    q.put((100, None))
    t = start()
    t.join()
