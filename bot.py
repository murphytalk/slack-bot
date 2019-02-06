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
    def __init__(self, channel, user_id, text, ts):
        self.channel = channel
        self.user = users[user_id] if user_id else ''
        self.text = text
        self.ts = ts
        self.mentioned_users = SlackEvent.parse_users_mentioned(text)

    def __str__(self):
        return "channel={},user={},ts={},mentioned_users={},text={}".format(self.channel, self.user, self.ts, self.mentioned_users, self.text)


class Command(object):
    pass


class Pinyin(Command):
    match = re.compile('^py *(.*)$')

    @staticmethod
    def run(raw_message):
        m = Pinyin.match.match(raw_message)
        if m:
            card1, card2 = py_gen.gen_cards(m.group(1))
            res = card1.front + ' ' + card1.back
            if card2:
                res += '\n' + card2.front + ' ' + card2.back
            return res

        return None


class URL(Command):
    @staticmethod
    def run(raw_message):
        try:
            url = raw_message[1:-1] if raw_message[0] == '<' and raw_message[-1] == '>' else raw_message
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
    if msg.text:
        for cmd in commands:
            result = cmd.run(msg.text)
            if result:
                print('RE',result)
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
            print(data)
            msg = Message(
                data['channel'],
                data['user'] if 'user' in data else None,
                data['text'],
                data['ts'])
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
