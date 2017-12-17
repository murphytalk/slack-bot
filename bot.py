#!/usr/bin/env pythoon
import os
import re
import time
# http://slackapi.github.io/python-slackclient/
from slackclient import SlackClient
from slackclient.user import User

READ_WEBSOCKET_DELAY = 1
BOT_USERNAME = os.environ.get("BOT_USERNAME")

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
users = {}


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


def parseSlackRTM(rtm_data):
    for data in rtm_data:
        data_type = data['type']
        if data_type == 'message':
            msg = Message(
                data['channel'],
                data['user'],
                data['text'],
                data['ts'])
            if msg.mentioned_users:
                print(msg.mentioned_users)
            print(msg.text)


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
