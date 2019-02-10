import inspect
import re
import sys
from commands.pinyin.wordpad import PinyinCardsGen
from commands._scraper import Scraper
from commands._anki import ANKI, ANKI2
assert ANKI, ANKI2  # silence flake8 complaing module imported but not used


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
    commands = {c.__name__: c.__doc__.strip() for n, c in inspect.getmembers(sys.modules[__name__], inspect.isclass) if c.__doc__}

    @staticmethod
    def run(cmd):
        return HELP.commands[cmd.upper()] if cmd and len(cmd) > 0 else '\n'.join([doc.split('\n')[0] for c, doc in HELP.commands.items()])


matcher = re.compile('^([A-Za-z]+) *(.*)$')


def dispatch(msg):
    if msg.startswith('http://') or msg.startswith('https://'):
        return URL.run(msg)
    else:
        match_res = matcher.match(msg)
        if match_res:
            cmd = match_res.group(1).upper()
            cls = getattr(sys.modules[__name__], cmd, None)
            return cls.run(match_res.group(2)) if cls else None
