#!/usr/bin/env python
import inspect
import os
import re
import sys
import time
from urllib.parse import urlparse
# http://slackapi.github.io/python-slackclient/
from slackclient import SlackClient
from slackclient.user import User

from pinyin.wordpad import PinyinCardsGen
from scraper import crawl

READ_WEBSOCKET_DELAY = 1
BOT_USERNAME = os.environ.get("BOT_USERNAME")

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
users = {}

py_gen = PinyinCardsGen()


class SlackEvent(object):
    @classmethod
    def parse_users_mentioned(cls, text):
        return [
            users[uid[2:-1]]
            for uid in re.findall(r'<@U.*?>', text)
            if uid[2:-1] in users
        ]


class Message(SlackEvent):
    def __init__(self, raw_message):
        if 'user' in raw_message:
            self.mentioned_users = SlackEvent.parse_users_mentioned(raw_message['user'])
        for k, v in raw_message.items():
            setattr(self, k, v)

    def __str__(self):
        return 'Message\n' + '\n'.join(["{}={}".format(k, v) for k, v in self.__dict__.items()])


class Command(object):
    pass


class Pinyin(Command):
    match = re.compile('^py *(.*)$')

    @staticmethod
    def run(text):
        m = Pinyin.match.match(text)
        if m:
            card1, card2 = py_gen.gen_cards(m.group(1))
            res = card1.front + ' ' + card1.back
            if card2:
                res += '\n' + card2.front + ' ' + card2.back
            return res

        return None


class URL(Command):
    @staticmethod
    def run(text):
        try:
            url = text[1:-1] if text[0] == '<' and text[-1] == '>' else text
            uri = urlparse(url)
            if uri and uri.scheme in ('http', 'https'):
                items = crawl(url)
                if items:
                    return '\n'.join([item['text'] for item in items if 'text' in item])
        except Exception:
            pass
        return None


commands = [v for k, v in inspect.getmembers(sys.modules[__name__], inspect.isclass)
            if issubclass(v, Command) and hasattr(v, 'run')]


def dispatch_msg(msg):
    if hasattr(msg, 'text'):
        for cmd in commands:
            result = cmd.run(msg.text)
            if result:
                slack_client.api_call(
                    "chat.postMessage",
                    channel=msg.channel,
                    text=result,
                    thread_ts=msg.ts
                )



def parseSlackRTM(rtm_data):
    for data in rtm_data:
        data_type = data['type']
        if data_type == 'message':
            msg = Message(data)
            print(msg)
            dispatch_msg(msg)


if __name__ == "__main__":
    userlst_call = slack_client.api_call("users.list")
    if userlst_call.get('ok'):
        users = {
            u['id']: User(
                None,
                u['name'],
                u['id'],
                u['real_name'],
                u['tz'],
                u['profile'].get('email')
            )
            for u in userlst_call.get('members') if not u['deleted']
        }

        if slack_client.rtm_connect():
            print("Connected to Slack")
            while True:
                parseSlackRTM(slack_client.rtm_read())
                time.sleep(READ_WEBSOCKET_DELAY)
