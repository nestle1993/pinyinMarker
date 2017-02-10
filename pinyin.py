#! /usr/bin/python
# -*- encoding: utf-8 -*-
#
# PinyinMarker Lib
#
# Usuage:
#       marker = simple_mandarin_marker([YOUR_MARKING_FILES])
#       where marking.dat is marking file.
#       marker.mark(chinese_string)
#
# =============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
VER = sys.version[0]


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def is_light_tone(pinyin):
    for l in pinyin:
        if l in "0123456789":
            return False
    return True


class PinyinUnit(object):
    def __init__(self, pinyin, freq):
        self._pinyin = pinyin
        self._freq = freq
        self._length = len(pinyin)

    @property
    def pinyin(self):
        return self._pinyin

    @property
    def freq(self):
        return self._freq

    @freq.setter
    def freq(self, value):
        self._freq = value

    @property
    def length(self):
        return self._length


class MarkUnit:
    def __init__(self, chinese, pinyin_units):
        self._chinese = chinese
        self._pinyin_units = dict([(' '.join(item.pinyin), item)
                                   for item in pinyin_units])

    def merge_pinyin(self, pinyin_units):
        for pinyin_unit in pinyin_units:
            key = ' '.join(pinyin_unit.pinyin)
            if key in self._pinyin_units.keys():
                self._pinyin_units[key].freq += pinyin_unit.freq
            else:
                self._pinyin_units[key] = pinyin_unit

    def merge_mark_unit(self, markunit):
        if self.chinese != markunit.chinese:
            return
        self._pinyin_units = self.merge(markunit.pinyin_units)

    @property
    def chinese(self):
        return self._chinese

    @property
    def pinyin_units(self):
        return self._pinyin_units


def pinyin_comp(a, b):
    a = a[0]
    b = b[0]
    if a.length > b.length:
        return -1
    if a.length < b.length:
        return 1
    if a.freq > b.freq:
        return -1
    if a.freq < b.freq:
        return 1
    return 0


if VER == '3':
    from functools import cmp_to_key
    pinyin_key = cmp_to_key(pinyin_comp)


class PinyinMarker:
    def add_pinyin_units(self, chinese, pinyin_units):
        if chinese in self._mark_dict:
            self._mark_dict[chinese].merge_pinyin(pinyin_units)
        else:
            self._mark_dict[chinese] = MarkUnit(chinese, pinyin_units)

    def add_mark_unit(self, markunit):
        if markunit.chinese in self._mark_dict:
            self._mark_dict[markunit.chinese].merge_mark_unit(markunit)
        else:
            self._mark_dict[markunit.chinese] = \
                MarkUnit(markunit.chinese, markunit.pinyin_units)

    def merge_dict(self, mark_dict):
        for mark_unit in mark_dict.values():
            self.add_mark_unit(mark_unit)

    def merge_dat_file(self, marking_files):
        for marking_file in marking_files:
            with open(marking_file, 'r') as fin:
                while True:
                    line = fin.readline()
                    if not line:
                        break
                    if VER == '2':
                        line = unicode(line, 'utf-8')
                    line = line.replace("\n", "")
                    line = line.replace(u'・', '')
                    units = line.split('|')
                    freq = 1
                    if len(units) > 2:
                        freq = int(units[2])
                    self.add_pinyin_units(units[0],
                                          [PinyinUnit(units[1].split(' '),
                                                      freq)])

    def merge_polyphone_dict(self, poly_files):
        for poly_file in poly_files:
            with open(poly_file, 'r') as fin:
                while True:
                    line = fin.readline()

                    if not line:
                        break
                    if VER == '2':
                        line = unicode(line, 'utf-8')
                    line = line.replace("\n", "")
                    line = line.replace(u'・', '')
                    units = line.split('|')
                    self.poly_dict[units[0]] = True

    def construct_light_tone_conversion_dict(self):
        self._light_tone_conversion = {}
        # import IPython
        # IPython.embed()
        for chinese in self._mark_dict:
            # except letter and '_'
            if len(chinese) == 1 and not is_ascii(chinese):
                before_light_tone = ""
                for pinyin in self._mark_dict[chinese].pinyin_units:
                    if is_light_tone(pinyin):
                        before_light_tone = pinyin
                        after_light_tone = ""
                        after_light_tone_freq = 0
                        for conversion in self._mark_dict[chinese].pinyin_units:
                            if not is_light_tone(conversion) and \
                               before_light_tone == conversion[:-1] and \
                               self._mark_dict[chinese].pinyin_units[conversion].freq >= after_light_tone_freq:
                                after_light_tone = conversion
                                after_light_tone_freq = self._mark_dict[chinese].pinyin_units[conversion].freq

                        if after_light_tone == "":
                            if before_light_tone == "<null>":
                                continue
                            else:
                                after_light_tone = before_light_tone + "1"
                        self._light_tone_conversion[(chinese, before_light_tone)] = after_light_tone

        self._light_tone_conversion[('儿', 'r')] = 'er2'
        self._light_tone_conversion[('袮', 'ni')] = 'mi2'
        self._light_tone_conversion[('伬', "ze")] = "chi3"
        self._light_tone_conversion[('母', "m")] = "mu3"

    def __init__(self, mark_dict=dict(), marking_files=[],
                 poly_dict=dict(), poly_files=[], convert_light_tone=False,
                 replace_unknown_to_tag=True):
        self._mark_dict = mark_dict
        self._convert_light_tone = convert_light_tone
        self.merge_dat_file(marking_files)

        self._poly_dict = poly_dict
        self.merge_polyphone_dict(poly_files)
        if self._convert_light_tone:
            self.construct_light_tone_conversion_dict()
        self._replace_unknown_to_tag = replace_unknown_to_tag

    def mark_only_unicode(self, tokens, multi_result=False):
        pinyins = []
        sentence_length = len(tokens)
        for pos in range(sentence_length):
            marks = []
            # process according to whether chinese is polyphone or not
            if not tokens[pos] in self.poly_dict:
                if tokens[pos] in self.mark_dict:
                    for pinyin_unit in self.mark_dict[tokens[pos]].\
                            pinyin_units.values():
                        marks.append([pinyin_unit, 0])
            else:
                for length in range(6):
                    for l_length in range(length + 1):
                        l_pos = pos - l_length
                        r_pos = pos + length - l_length
                        key_s = ''.join(tokens[l_pos:r_pos])
                        if l_pos >= 0 and r_pos > pos and \
                           r_pos <= sentence_length \
                           and key_s in self.mark_dict:
                            for pinyin_unit in \
                                self.mark_dict[key_s].\
                                    pinyin_units.values():
                                marks.append([pinyin_unit, pos - l_pos])
            if VER == '2':
                marks.sort(pinyin_comp)
            elif VER == '3':
                marks.sort(key=pinyin_key)

            if len(marks) == 0:
                pinyins.append(
                    '<unk>' if self._replace_unknown_to_tag else tokens[pos])
            else:
                origin_pinyin = marks[0][0].pinyin[marks[0][1]]
                if self._convert_light_tone:
                    if (tokens[pos], origin_pinyin) in self._light_tone_conversion:
                        origin_pinyin = self._light_tone_conversion[
                            (tokens[pos], origin_pinyin)]
                pinyin_candidates = [origin_pinyin]

                total_freq = 0
                for mark in marks:
                    total_freq += mark[0].freq
                filtered_marks = []
                for mark in marks:
                    if float(mark[0].freq) / total_freq >= 0.01:
                        filtered_marks.append(mark)

                for mark in filtered_marks:
                    pinyin = mark[0].pinyin[mark[1]]
                    if self._convert_light_tone:
                        if (tokens[pos], pinyin) in self._light_tone_conversion:
                            pinyin = self._light_tone_conversion[
                                (tokens[pos], pinyin)]
                    repeat = False
                    for pinyin_candidate in pinyin_candidates:
                        if pinyin == pinyin_candidate:
                            repeat = True
                            break
                    if not repeat:
                        pinyin_candidates.append(pinyin)

                if multi_result:
                    pinyins.append("|".join(pinyin_candidates))
                else:
                    pinyins.append(pinyin_candidates[0])

        return pinyins

    def mark(self, tokens, multi_result=False):
        ret = []
        ll = 0
        for i in range(len(tokens)):
            if tokens[i] == u'<eos>' or tokens[i] == u'<sos>':
                ret.extend(self.mark_only_unicode(tokens[ll:i], multi_result))
                ret.append('<null>')
                ll = i + 1
        if ll != len(tokens):
            ret.extend(self.mark_only_unicode(tokens[ll:len(tokens)], multi_result))
        return ret

    @property
    def mark_dict(self):
        return self._mark_dict

    @property
    def poly_dict(self):
        return self._poly_dict


class BasicMarkerWithTone(PinyinMarker):
    def __init__(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        PinyinMarker.__init__(self, marking_files=[
            os.path.join(file_path, 'clean_janx_phrases.dat'),
            os.path.join(file_path, 'clean_aizuyan_words.dat'),
            os.path.join(file_path, 'single_word.dat')],
            poly_files=[os.path.join(file_path, 'polyphone.dat')],
            convert_light_tone=False,
            replace_unknown_to_tag=True)


class BasicMarkerWithToneKeepUnknown(PinyinMarker):
    def __init__(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        PinyinMarker.__init__(self, marking_files=[
            os.path.join(file_path, 'clean_janx_phrases.dat'),
            os.path.join(file_path, 'clean_aizuyan_words.dat'),
            os.path.join(file_path, 'single_word.dat')],
            poly_files=[os.path.join(file_path, 'polyphone.dat')],
            convert_light_tone=False,
            replace_unknown_to_tag=False)


class MarkerWithoutLightTone(PinyinMarker):
    def __init__(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        PinyinMarker.__init__(self, marking_files=[
            os.path.join(file_path, 'clean_janx_phrases.dat'),
            os.path.join(file_path, 'clean_aizuyan_words.dat'),
            os.path.join(file_path, 'single_word.dat')],
            poly_files=[os.path.join(file_path, 'polyphone.dat')],
            convert_light_tone=True)


class MarkerWithoutLightToneKeepUnknown(PinyinMarker):
    def __init__(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        PinyinMarker.__init__(self, marking_files=[
            os.path.join(file_path, 'clean_janx_phrases.dat'),
            os.path.join(file_path, 'clean_aizuyan_words.dat'),
            os.path.join(file_path, 'single_word.dat')],
            poly_files=[os.path.join(file_path, 'polyphone.dat')],
            convert_light_tone=True,
            replace_unknown_to_tag=False)


class MarkerInitialFinalXiaoyun(MarkerWithoutLightTone):
    def __init__(self):
        from pkg.reg_dict.initial_final_without_light_tone import \
            initials, blocks, independents
        self._initials = initials
        self._blocks = set(blocks)
        self._independents = set(independents)
        MarkerWithoutLightTone.__init__(self)

    def mark(self, tokens):
        pinyin_tokens = MarkerWithoutLightTone.mark(self, tokens)
        iftokens = []
        for pinyin_token in pinyin_tokens:
            if pinyin_token in self._blocks:
                iftokens.append(pinyin_token)
            elif 'g_' + pinyin_token in self._independents:
                iftokens.append('g_' + pinyin_token)
            else:
                for initial in self._initials:
                    if pinyin_token.startswith(initial):
                        iftokens.append(initial)
                        iftokens.append(pinyin_token.lstrip(initial))
                        break

        if VER == '3':
            return iftokens
        elif VER == '2':
            return map(unicode, iftokens)


class MarkerInitialFinalZhaoxiong(MarkerWithoutLightTone):
    def __init__(self):
        from pkg.reg_dict.initial_final_without_light_tone import \
            initials, blocks, independents
        self._initials = initials
        self._blocks = set(blocks)
        self._independents = set(independents)
        MarkerWithoutLightTone.__init__(self)

    def mark(self, tokens):
        pinyin_tokens = MarkerWithoutLightTone.mark(self, tokens)
        iftokens = []
        for pinyin_token in pinyin_tokens:
            if pinyin_token in self._blocks:
                iftokens.append(pinyin_token)
            elif 'g_' + pinyin_token in self._independents:
                iftokens.extend(['<b>', pinyin_token])
            else:
                for initial in self._initials:
                    if pinyin_token.startswith(initial):
                        iftokens.append(initial)
                        iftokens.append(pinyin_token.lstrip(initial))
                        break

        if VER == '3':
            return iftokens
        elif VER == '2':
            return map(unicode, iftokens)

class MarkerWithoutLightTone_Eng(PinyinMarker):
    def __init__(self):
        file_path = os.path.dirname(os.path.abspath(__file__))
        PinyinMarker.__init__(self, marking_files=[
            os.path.join(file_path, 'clean_janx_phrases.dat'),
            os.path.join(file_path, 'clean_aizuyan_words.dat'),
            os.path.join(file_path, 'single_word.dat'),
            os.path.join(file_path, 'letter.dat')],
            poly_files=[os.path.join(file_path, 'polyphone.dat')],
            convert_light_tone=True,
            replace_unknown_to_tag=True)

if __name__ == "__main__":
    marker = BasicMarkerWithTone()
    # file_path = os.path.dirname(os.path.abspath(__file__))
    # marker = load_single_word_marker(
    #     [os.path.join(file_path, 'clean_janx_phrases.dat'),
    #      os.path.join(file_path, 'clean_aizuyan_words.dat')],
    #     "single_word.dat")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_sentence", default="",
                        help="converting sentence")
    flags = parser.parse_args()
    ret = marker.mark(flags.input_sentence.decode('utf-8').split())
    print(ret)
