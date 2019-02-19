#!/usr/bin/env python
import re
import os
import time

# http://slackapi.github.io/python-slackclient/
from slackclient import SlackClient
from slackclient.user import User

from commands import dispatch

READ_WEBSOCKET_DELAY = 1
BOT_USERNAME = os.environ.get("BOT_USERNAME")

slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))
users = {}


class SlackEvent(object):
    @classmethod
    def parse_users_mentioned(cls, text):
        global users
        return [users[uid[2:-1]] for uid in re.findall(r"<@U.*?>", text) if uid[2:-1] in users]


class Message(SlackEvent):
    def __init__(self, raw_message):
        if "user" in raw_message:
            self.mentioned_users = SlackEvent.parse_users_mentioned(raw_message["user"])
        for k, v in raw_message.items():
            setattr(self, k, v)

    def __str__(self):
        return (
            "=== Message ===\n"
            + "\n".join(["{}={}".format(k, v) for k, v in self.__dict__.items()])
            + "\n===============\n"
        )


def parseSlackRTM(rtm_data):
    for data in rtm_data:
        print("Raw Data:", data)

        if "type" not in data:
            continue

        if data["type"] != "message":
            continue

        msg = Message(data)
        print(msg)
        if not hasattr(msg, "text") or not hasattr(msg, "user"):
            continue

        text = msg.text.strip()
        uid = msg.user.strip()
        # Slack quotes URL with <>
        text = text[1:-1] if text[0] == "<" and text[-1] == ">" else text
        result = dispatch(text, uid)
        if result:
            # the documentation is wrong
            # https://github.com/slackapi/python-slackclient/blob/master/slackclient/client.py#L246
            slack_client.rtm_send_message(msg.channel, result, None)  # msg.ts)


def run():
    userlst_call = slack_client.api_call("users.list")
    if userlst_call.get("ok"):
        users = {
            u["id"]: User(
                None, u["name"], u["id"], u["real_name"], u["tz"], u["profile"].get("email")
            )
            for u in userlst_call.get("members")
            if not u["deleted"]
        }
        print("Users", users)

        if slack_client.rtm_connect():
            print("Connected to Slack")
            while True:
                parseSlackRTM(slack_client.rtm_read())
                time.sleep(READ_WEBSOCKET_DELAY)


if __name__ == "__main__":
    run()
