# coding:utf-8

# from __future__ import division
from collections import defaultdict
import math
import io
from JieBa import JieBa

LOG_LIM = 1E-300
endtag = [ '。/w', '？/w', '！/w', '；/w', '?/w', '!/w','./w']
#endtag = ['./m', '!/m', '?/m', '。/w', '？/w', '！/w', '；/w', '，/w', ',/w']
#endtag = [ '。/PU', '？/PU', '！/PU', './PU']
#endtag = ['但是/c','就是/d','只是/c','不过/c','可是/c','但/c']


class SentimentWordDiscover:

    pos_dict = None
    neg_dict = None
    documents = None
    all_words = None
    jieba = None

    def __init__(self, pos_path, neg_path, doc_path):
        self.jieba = JieBa()
        # self.pos_dict = ["好看", "值得", "杰作", "天才", "好评"]
        self.pos_dict = set(self.read_file_by_line(pos_path))
        # self.neg_dict = ["难看", "低分", "难受", "浪费", "一般"]
        self.neg_dict = set(self.read_file_by_line(neg_path))
        self.__load_docs(self.read_file_by_line(doc_path))
        self.process()

    def __load_docs(self, lines):
        self.documents = []
        self.all_words = set()
        for line in lines:
            words = set(self.jieba.segmentation(line))
            self.documents.append(words)
            self.all_words.update(words)

    @staticmethod
    def read_file_by_line(path):
        lines = []
        with io.open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line != "":
                    lines.append(line)
        return lines

    def calculate_pmi(self, word1, word2):
        show_together = self.__statistic_2words_in_docs(word1, word2)
        if show_together == 0:
            return 0
        w1_show = self.__statistic_word_in_docs(word1)
        w2_show = self.__statistic_word_in_docs(word2)
        return math.log(len(self.documents) * show_together * 1.0 / (w1_show * w2_show), 2)

    def __statistic_word_in_docs(self, word):
        in_count = 0
        for document in self.documents:
            if word in document:
                in_count += 1
        return in_count

    def __statistic_2words_in_docs(self, word1, word2):
        in_count = 0
        for document in self.documents:
            if word1 in document and word2 in document:
                in_count += 1
        return in_count

    def process(self):
        for word in self.all_words:
            if word in self.pos_dict or word in self.neg_dict:
                continue
            val = 0.0
            for pos_word in self.pos_dict:
                val += self.calculate_pmi(word, pos_word)
            for neg_word in self.neg_dict:
                val -= self.calculate_pmi(word, neg_word)
            print word + ":" + str(val)

if __name__ == '__main__':

    swd = SentimentWordDiscover("../dict/pos_dict.txt", "../dict/neg_dict.txt", "../data/documents.txt")
    
    print 'end'
