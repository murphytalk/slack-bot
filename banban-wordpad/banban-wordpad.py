#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os,codecs
from optparse import OptionParser
from collections import defaultdict
from langconv import *
from random import shuffle

def build_hanzi_pinyin_map():
    hanzi_pinyin_map = defaultdict(list)
    code_file = os.path.dirname(os.path.realpath(__file__)) + '/pinyin_unicode.txt'
    for line in codecs.open(code_file,'r','utf_16').readlines():
        fields = line.split()
        pinyin = fields[0]
        for hanzi in fields[1]:
            hanzi_pinyin_map[hanzi].append(pinyin)
    
    return hanzi_pinyin_map

class FlashCard:
    def __init__(self,front):
        self.front = front
        self.back  = ''

    def write_to_back(self,word):
        self.back += word

class AnkiFile:
    def __init__(self,file_out):
        #the encoding must be utf-8 to import to Anki
        self.file_obj = codecs.open(file_out, 'wb','utf-8') if (file_out and file_out != '-') else sys.stdout
        self.words = set()

    def write(self,card):
        if card.front not in self.words:
            self.file_obj.write(card.front)
            self.file_obj.write(';')
            self.file_obj.write(card.back)
            self.file_obj.write('\n')
            self.words.add(card.front)


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


    file_in = codecs.open(options.file_in,'r',encoding) if (options.file_in and options.file_in != '-') else sys.stdin
    anki = AnkiFile(options.file_out)

    hz2py = build_hanzi_pinyin_map()
    simplified2traditional = Converter('zh-hant')

    cards = []

    for line in file_in.readlines():
        fields = line.split()
        if fields:            
            hanzi = fields[0]
            card = FlashCard(hanzi)
            cards.append(card)
            for hz in hanzi:
                if hz in hz2py:
                    for py in hz2py[hz]:
                        card.write_to_back(py+' ')
                else:
                    card.back('[NOT FOUND] ')
                    
            fanti = FlashCard(simplified2traditional.convert(hanzi))
            fanti.write_to_back(card.back)
            cards.append(fanti)

    shuffle(cards)
    for c in cards:
       anki.write(c)

