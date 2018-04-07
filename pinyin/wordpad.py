#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import codecs
from optparse import OptionParser
from collections import defaultdict
from pinyin.langconv import Converter
from random import shuffle


def build_hanzi_pinyin_map():
    hanzi_pinyin_map = defaultdict(list)
    code_file = os.path.dirname(os.path.realpath(__file__)) + '/pinyin_unicode.txt'
    for line in codecs.open(code_file, 'r', 'utf_16').readlines():
        fields = line.split()
        pinyin = fields[0]
        for hanzi in fields[1]:
            hanzi_pinyin_map[hanzi].append(pinyin)

    return hanzi_pinyin_map


class FlashCard:
    def __init__(self, front):
        self.front = front
        self.back = ''

    def write_to_back(self, word):
        self.back += word


class AnkiFile:
    def __init__(self, file_out):
        # the encoding must be utf-8 to import to Anki
        self.file_obj = codecs.open(file_out, 'wb', 'utf-8') if (file_out and file_out != '-') else sys.stdout
        self.words = set()

    def write(self, card):
        if card.front not in self.words:
            self.file_obj.write(card.front)
            self.file_obj.write(';')
            self.file_obj.write(card.back)
            self.file_obj.write('\n')
            self.words.add(card.front)


class PinyinCardsGen(object):
    def __init__(self):
        self.hz2py = build_hanzi_pinyin_map()
        self.simplified2traditional = Converter('zh-hant')

    def gen_cards(self, simplified_chinese):
        card1 = FlashCard(simplified_chinese)
        for hz in simplified_chinese:
            if hz in self.hz2py:
                for py in self.hz2py[hz]:
                    card1.write_to_back(py + ' ')
            else:
                card1.back('[NOT FOUND] ')

        traditional_chinese = self.simplified2traditional.convert(simplified_chinese)
        if simplified_chinese == traditional_chinese:
            card2 = None
        else:
            card2 = FlashCard(traditional_chinese)
            card2.write_to_back(card1.back)
        return card1, card2


if __name__ == '__main__':
    encoding = 'gbk'

    parser = OptionParser()
    parser.add_option('-e', type='string', dest='encoding',
                      help='encoding')
    parser.add_option('-i', type='string', dest='file_in',
                      help='input file (- or omitted for stdin)')
    parser.add_option('-o', type='string', dest='file_out',
                      help='output file (omitted for stdout)')

    (options, args) = parser.parse_args()

    if options.encoding:
        encoding = options.encoding

    file_in = codecs.open(options.file_in, 'r', encoding) if (options.file_in and options.file_in != '-') else sys.stdin
    anki = AnkiFile(options.file_out)

    py_gen = PinyinCardsGen()
    cards = []

    for line in file_in.readlines():
        fields = line.split()
        if fields:
            hanzi = fields[0]
            card1, card2 = py_gen.gen_cards(hanzi)
            cards.append(card1)
            if card2:
                cards.append(card2)

    shuffle(cards)
    for c in cards:
        anki.write(c)
