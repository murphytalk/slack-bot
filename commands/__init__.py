import inspect
import re
import sys
from commands.pinyin.wordpad import PinyinCardsGen
from commands._scraper import Scraper
from commands._anki import ANKI, ANKI2
assert ANKI, ANKI2  # silence flake8 complaing module imported but not used


_matcher = re.compile('^([A-Za-z]+) *(.*)$')


def _parse_cmd(cmd):
    match_res = _matcher.match(cmd)
    return getattr(sys.modules[__name__], match_res.group(1).upper(), None), match_res.group(2) if match_res else None


class URL(object):
    @staticmethod
    def run(url):
        items = Scraper.run(url)
        return '\n'.join([item['text'] for item in items if 'text' in item]) if items else None


class PY(object):
    """py <Chinese word>
    Return pinyin of the given chinese word, along with traditional chinese (if available)
    """
    py_gen = PinyinCardsGen()

    @staticmethod
    def run(text):
        card1, card2 = PY.py_gen.gen_cards(text)
        res = card1.front + ' ' + card1.back
        if card2:
            res += '\n' + card2.front + ' ' + card2.back
        return res


class HELP(object):
    """help [command]
    Show a list of commands that I understand, or full command help if the command is specified.
    """

    @staticmethod
    def run(cmd):
        if cmd and len(cmd) > 0:
            cls, param = _parse_cmd(cmd)
            return cls.__doc__ if cls else None
        else:
            return '\n'.join([c.__doc__.split()[0] for n, c in inspect.getmembers(sys.modules[__name__], inspect.isclass) if c.__doc__])


def dispatch(msg):
    if msg.startswith('http://') or msg.startswith('https://'):
        return URL.run(msg)
    else:
        cls, param = _parse_cmd(msg)
        return cls.run(param) if cls else None