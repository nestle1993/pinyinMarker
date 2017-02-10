# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import sys

from pinyin import BasicMarkerWithTone, MarkerWithoutLightTone, \
    MarkerWithoutLightTone_Eng

VER = sys.version[0]


def _utf8(s):
    if VER == '2':
        return s.decode('utf-8')
    else:
        return s


class MarkerTest(unittest.TestCase):
    def MarkerTest(self, marker, chinese, pinyins):
        ret = marker.mark(chinese)
        self.assertEqual(ret, pinyins)

    def testBasicMarker(self):
        marker = BasicMarkerWithTone()
        with open("pinyin_tone_test.txt", "r") as fin:
            while True:
                line_chinese = fin.readline()
                if not line_chinese:
                    break
                line_pinyin = fin.readline()
                if not line_pinyin:
                    break
                line_chinese = _utf8(line_chinese).\
                    replace('\n', '').replace(' ', '')
                line_pinyin = _utf8(line_pinyin).\
                    replace('\n', '').split()
                self.MarkerTest(marker, line_chinese, line_pinyin)

    def testMarkerWithoutTone(self):
        marker = MarkerWithoutLightTone()
        with open("pinyin_without_light_tone_test.txt", "r")\
                as fin:
            while True:
                line_chinese = fin.readline()
                if not line_chinese:
                    break
                line_pinyin = fin.readline()
                if not line_pinyin:
                    break
                line_chinese = _utf8(line_chinese).\
                    replace('\n', '').replace(' ', '')
                line_pinyin = _utf8(line_pinyin).\
                    replace('\n', '').split()
                self.MarkerTest(marker, line_chinese, line_pinyin)

    def testMarkerWithoutTone_Eng(self):
        marker = MarkerWithoutLightTone_Eng()
        with open(
            "pinyin_without_light_tone_eng_test.txt",
                "r") as fin:
            while True:
                line_chinese = fin.readline()
                if not line_chinese:
                    break
                line_pinyin = fin.readline()
                if not line_pinyin:
                    break
                line_chinese = _utf8(line_chinese).\
                    replace('\n', '').replace(' ', '')
                line_pinyin = _utf8(line_pinyin).replace('\n', '').split()
                self.MarkerTest(marker, line_chinese, line_pinyin)

if __name__ == "__main__":
    unittest.main()
