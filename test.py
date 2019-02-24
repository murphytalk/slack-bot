#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import inspect
from unittest.mock import patch
import commands


class TestCommands(unittest.TestCase):
    def test_unknown_cmd(self):
        assert commands.dispatch("doesnotexist") is None

    def test_PY(self):
        expected = "测试 cè shì \n測試 cè shì "
        assert commands.dispatch("py 测试") == expected
        assert commands.dispatch("Py 测试") == expected

    @patch("commands.URL.run")
    def test_URL(self, url_run):
        commands.dispatch("http://abc.com")
        assert url_run.called

    def test_HELP_list(self):
        cmds = set(
            [n.lower() for n, c in inspect.getmembers(commands, inspect.isclass) if c.__doc__]
        )
        for h in commands.dispatch("help").split("\n"):
            m = commands._matcher.match(h)
            assert m
            assert m.group(1).lower() in cmds

    def test_HELP_help(self):
        res = commands.dispatch("help py")
        assert res
        assert res.startswith("py ")
        assert "\n" in res

    @patch("commands.ANKI._get_user")
    @patch("commands.ANKI.deck")
    @patch("commands.ANKI._add")
    @patch("commands.ANKI.user")
    def test_ANKI_mode(self, user, add, deck, get_user):
        get_user.return_value = 'user'

        assert not commands.ANKI.enabled

        commands.dispatch("anki")
        assert commands.ANKI.enabled

        commands.dispatch("user me")
        user.assert_called_with("me")

        commands.dispatch("deck my")
        deck.assert_called_with("my")

        commands.dispatch("deck")
        deck.assert_called_with("")

        assert (
            commands.dispatch("add f1, f2")
            == 'No deck is selected'
        )

        commands.ANKI.model_fields = ['F1']
        assert (
            commands.dispatch("add f1, f2")
            == 'Fields number is incorrect, expected fields are F1'
        )

        commands.ANKI.model_fields = ['F1', 'F2']
        commands.dispatch("add f1, f2")
        add.assert_called_with(['f1', 'f2'])

        assert (
            commands.dispatch("unknown")
            == commands.ANKI.__doc__
        )

        assert (
            commands.dispatch("unknown param")
            == commands.ANKI.__doc__
        )

        commands.dispatch("off")
        assert not commands.ANKI.enabled


if __name__ == "__main__":
    unittest.main()
