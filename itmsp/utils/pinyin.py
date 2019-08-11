# coding: utf-8
# Author: cleverdeng

import os


class PinYin(object):
    def __init__(self, dict_file="install/initial_data/word.data"):
        self.word_dict = {}
        self.dict_file = dict_file
        self.available = False

    def load_word(self):
        if not os.path.exists(self.dict_file):
            raise IOError("NotFoundFile: {}".format(self.dict_file))
        self.available = True
        with file(self.dict_file) as f_obj:
            for f_line in f_obj.readlines():
                try:
                    line = f_line.split('    ')
                    self.word_dict[line[0]] = line[1]
                except:
                    line = f_line.split('   ')
                    self.word_dict[line[0]] = line[1]

    def hanzi2pinyin(self, string=""):
        string = string.replace(" ", "")
        result = []
        if not isinstance(string, unicode):
            string = string.decode("utf-8")
        for char in string:
            if char in ' -\n':
                continue
            key = '%X' % ord(char)
            result.append(self.word_dict.get(key, char).split()[0][:-1].lower())
        return result

    def hanzi2pinyin_split(self, string="", split=""):
        result = self.hanzi2pinyin(string=string)
        return split.join(result)

    def hanzi2firstletter(self, string=""):
        result = ""
        for py in self.hanzi2pinyin(string=string):
            result += py[:1]
        return result
