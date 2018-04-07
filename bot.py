#!/usr/bin/env python
import os
import re
import time
# http://slackapi.github.io/python-slackclient/
from slackclient import SlackClient
from slackclient.user import User

from pinyin.wordpad import PinyinCardsGen

READ_WEBSOCKET_DELAY = 1
BOT_USERNAME = os.environ.get("BOT_USERNAME")

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
users = {}

py_gen = PinyinCardsGen()


class SlackEvent:
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
        self.user = users[user_id]
        self.text = text
        self.ts = ts
        self.mentioned_users = SlackEvent.parse_users_mentioned(text)

    def __unicode__(self):
        print(u"channel=%s,user=%s,ts=%s,mentioned_users=%s,text=%s" %
              (self.channel, self.user, self.ts, self.mentioned_users, self.text))


def dispatch_msg(msg):
    if msg.text:
        card1, card2 = py_gen.gen_cards(msg.text)
        print(card1.front, card1.back)
        if card2:
            print(card2.front, card2.back)


def parseSlackRTM(rtm_data):
    for data in rtm_data:
        data_type = data['type']
        if data_type == 'message':
            msg = Message(
                data['channel'],
                data['user'],
                data['text'],
                data['ts'])
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
