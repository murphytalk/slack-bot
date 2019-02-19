# -*- coding: utf-8 -*-
import os
import re
import requests


class ANKI(object):
    """anki <English word>[,<deck>]
    Look up dictionary and add the English word, pronunciation and meaning to Anki
    """

    pass


class ANKI2(object):
    """anki2
    Enable Anki continuous mode.
    When continuous mode is enabled, any message following that will be interpreted as Anki card.

    The message could be any of the following patterns:

    deck [deck name]
       Select a deck or list all decks

    user <user name>
       Select an anki user
       if user is not being explictily selected, the value of environment variable whose name is
       same as slack UID will be used.

    <front>,<back>
       add a card to Anki

    off
       exit Anki continuous mode.
    """

    # obviously this is not thread-safe, and we don't care
    enabled = False
    cmdPattern = re.compile(r"^(\w+)([^,]*)$", re.IGNORECASE)

    anki_server = os.environ.get("ANKI_SERVER", "http://127.0.0.1:27701")
    selected_user = None
    selected_deck = None

    @staticmethod
    def run(status):
        ANKI2.enabled = True
        return (
            "[Anki] continuous mode is on, anki user [{}], deck [{}]".format(
                ANKI2._get_user(), ANKI2.selected_deck
            )
            if ANKI2.enabled
            else None
        )

    @classmethod
    def process(cls, text):
        if text.strip().lower() == "off":
            cls.enabled = False
            return "Anki continuous mode is off"

        m = cls.cmdPattern.match(text)
        if m:
            try:
                func = getattr(cls, m.group(1))
                return func(m.group(2).strip())
            except AttributeError:
                return ANKI2.__doc__
        else:
            try:
                front, back = text.split(",")
                return cls.add(front.strip(), back.strip())
            except ValueError:
                return ANKI2.__doc__

    @classmethod
    def deck(cls, deck):
        decks = cls._query_anki('list_decks')
        if deck is None or deck == "":
            return '\n'.join([d['name'] for d in decks])
        else:
            for d in decks:
                if d['name'] == deck:
                    cls.selected_deck = deck
                    cls._query_anki('select_deck', {'deck': d['id']})
                    return 'Current deck is {}'.format(deck)
            return "Unknown deck " + deck

    @classmethod
    def user(cls, user):
        if user is None or user == "":
            return cls.__doc__
        cls.selected_user = user
        return 'Current user is {}'.format(user)

    @classmethod
    def add(cls, front, back):
        if cls.selected_user is None:
            try:
                cls.selected_user = os.environ.get(cls.slack_uid)
            except KeyError:
                return "Anki User not selected"

    @classmethod
    def _query_anki(cls, query, data={}):
        try:
            url = '{}/collection/{}/{}'.format(cls.anki_server, cls._get_user(), query)
            r = requests.post(url, json=data)
            return (r.json() if len(r.text) > 0 else None) if r and r.status_code == 200 else None
        except RuntimeError as e:
            return str(e)

    @classmethod
    def _get_user(cls):
        if cls.selected_user:
            return cls.selected_user
        else:
            cls.selected_user = os.environ.get(cls.slack_uid, None)
            if cls.selected_user:
                return cls.selected_user
            raise RuntimeError("Please select an Anki user first")
