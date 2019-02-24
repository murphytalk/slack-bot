# -*- coding: utf-8 -*-
import os
import re
import requests


class ANKI(object):
    """anki
    Enable Anki continuous mode.
    When continuous mode is enabled, any message following that will be interpreted as Anki card.

    The message could be any of the following patterns:

    user <user name>
       Select an anki user
       if user is not being explictily selected, the value of environment variable whose name is
       same as slack UID will be used.

    deck [deck name]
       Select a deck or list all decks

    fields
       list fields of selected deck

    add <field1>[,<field2>, ... , <field N>]
       add a card. The fields must match the order of the list returned by fields command

    off
       exit Anki continuous mode.
    """

    # obviously this is not thread-safe, and we don't care
    enabled = False
    cmdPattern = re.compile(r"^(\w+)(.*)$", re.IGNORECASE)

    anki_server = os.environ.get("ANKI_SERVER", "http://127.0.0.1:27701")
    selected_user = None
    selected_deck = None
    selected_model_id = None
    model_fields = None

    # HACKING - for reason I don't know some Anki deck query do not return model id
    # add deck id to model id mapping for those decks
    _MODEL_ID_OVERRIDES = {
        1_523_111_820_579: 1_352_475_098_963,
        1_523_111_828_093: 1_352_475_098_963,
    }

    @staticmethod
    def run(status):
        ANKI.enabled = True
        return (
            "[Anki] continuous mode is on, anki user [{}], deck [{}]".format(
                ANKI._get_user(), ANKI.selected_deck
            )
            if ANKI.enabled
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
                return ANKI.__doc__
        else:
            return ANKI.__doc__

    @classmethod
    def deck(cls, deck):
        decks = cls._query_anki("list_decks")
        if deck is None or deck == "":
            return "\n".join([d["name"] for d in decks])
        else:
            for d in decks:
                if d["name"] == deck:
                    # get deck model ID
                    print(d)
                    deck = cls._query_anki("deck/{}".format(d["id"]))
                    if not deck or isinstance(deck, str):
                        return (
                            deck if deck else "Is this a valid deck? {}".format(cls.selected_deck)
                        )
                    cls.selected_deck = deck["name"]
                    if "mid" in deck:
                        cls.selected_model_id = deck["mid"]
                    elif d["id"] in cls._MODEL_ID_OVERRIDES:
                        cls.selected_model_id = cls._MODEL_ID_OVERRIDES[d["id"]]
                    else:
                        return "Cannot find model id, consider to override ride model id for deck id {}".fomrat(
                            d["id"]
                        )

                    fields = cls._query_anki("model/{}/field_names".format(cls.selected_model_id))
                    if not fields or isinstance(fields, str):
                        return (
                            fields
                            if fields
                            else "Failed to query model ID={}".format(cls.selected_model_id)
                        )
                    cls.model_fields = fields

                    cls._query_anki("select_deck", {"deck": d["id"]})
                    return "Current deck is {}".format(cls.selected_deck)
            return "Unknown deck " + deck

    @classmethod
    def user(cls, user):
        if user is None or user == "":
            return cls.__doc__
        cls.selected_user = user
        return "Current user is {}".format(user)

    @classmethod
    def _add(cls, fields):
        try:
            cls._query_anki("add_note", {
                'model': cls.selected_model_id,
                'fields': dict(zip(cls.model_fields, fields))
            })
            return "Note added"
        except Exception as e:
            return str(e)

    @classmethod
    def add(cls, fields):
        if not cls.model_fields:
            return "No deck is selected"

        cls._get_user()
        f = [f.strip() for f in fields.strip().split(",")]

        if len(f) != len(cls.model_fields):
            return "Fields number is incorrect, expected fields are {}".format(
                ",".join(cls.model_fields)
            )

        return cls._add(f)

    @classmethod
    def _query_anki(cls, query, data={}):
        try:
            url = "{}/collection/{}/{}".format(cls.anki_server, cls._get_user(), query)
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

    @classmethod
    def fields(cls, f=None):
        if not cls.model_fields:
            return "Select a deck please!"

        return "\n".join(cls.model_fields)
