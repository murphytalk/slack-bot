# -*- coding: utf-8 -*-
import re


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

    deck <deck name>
       Select a deck

    user <user name>
       Select a user
       if user is not being explictily selected, the value of environment variable whose name is same as slack UID will be used.

    <front>,<back>
       add a card to Anki

    off
       exit Anki continuous mode.
    """

    # obviously this is not thread-safe, and we don't care
    enabled = False
    cmdPattern = re.compile(r"^(\w+) *([^,]*)$", re.IGNORECASE)

    selected_user = None
    selected_deck = None

    @staticmethod
    def run(status):
        ANKI2.enabled = status.strip().upper() == 'ON'
        return "[Anki] continuous mode is on" if ANKI2.enabled else None

    @classmethod
    def process(cls, text):
        if text.strip().lower() == "off":
            cls.enabled = False
            return "Anki continuous mode is off"

        m = cls.cmdPattern.match(text)
        if m:
            try:
                func = getattr(cls, m.group(1))
                return func(m.group(2))
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
        cls.selected_deck = deck

    @classmethod
    def user(cls, user):
        cls.selected_user = user

    @classmethod
    def add(cls, front, back):
        pass
