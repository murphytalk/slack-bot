import re
import sys
from commands.pinyin.wordpad import PinyinCardsGen
from commands._scraper import Scraper


class URL(object):
    @staticmethod
    def run(url):
        items = Scraper.run(url)
        return '\n'.join([item['text'] for item in items if 'text' in item]) if items else None


class PY(object):
    py_gen = PinyinCardsGen()

    @staticmethod
    def run(text):
        card1, card2 = PY.py_gen.gen_cards(text)
        res = card1.front + ' ' + card1.back
        if card2:
            res += '\n' + card2.front + ' ' + card2.back
        return res


class Anki(object):
    pass




matcher = re.compile('^([A-Za-z]+) *(.*)$')


def dispatch(msg):
    if msg.startswith('http://') or msg.startswith('https://'):
        return URL.run(msg)
    else:
        match_res = matcher.match(msg)
        if match_res:
            cmd = match_res.group(1).upper()
            cls = getattr(sys.modules[__name__], cmd)
            return cls.run(match_res.group(2)) if cls else None
