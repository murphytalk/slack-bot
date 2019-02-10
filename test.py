#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import inspect
from unittest.mock import patch
import commands


class TestCommands(unittest.TestCase):
    def test_unknown_cmd(self):
        assert commands.dispatch('doesnotexist') is None

    def test_PY(self):
        expected = '测试 cè shì \n測試 cè shì '
        assert commands.dispatch('py 测试') == expected
        assert commands.dispatch('Py 测试') == expected

    @patch('commands.URL.run')
    def test_URL(self, url_run):
        commands.dispatch('http://abc.com')
        assert url_run.called

    def test_HELP_list(self):
        cmds = set([n.lower() for n, c in inspect.getmembers(commands, inspect.isclass) if c.__doc__])
        for h in commands.dispatch('help').split('\n'):
            m = commands._matcher.match(h)
            assert m
            assert m.group(1).lower() in cmds

    def test_HELP_help(self):
        res = commands.dispatch('help py')
        assert res
        assert res.startswith('py ')
        assert '\n' in res


if __name__ == '__main__':
    unittest.main()
