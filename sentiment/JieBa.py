# coding:utf-8
import jieba
import jieba.posseg as posseg


class JieBa:

    stopwords = None

    def __init__(self):
        jieba.load_userdict('../dict/word_dict.txt')
        self.stopwords = self.read_lines("../dict/stop_words.txt")  # 读取停用词表

    # 分词，返回List
    @staticmethod
    def segmentation(sentence):
        seg_list = jieba.cut(sentence)
        seg_result = []
        for w in seg_list:
            seg_result.append(w)
        return seg_result

    # 分词，词性标注，词和词性构成一个元组
    # def postagger(self, sentence):
    #     pos_data = posseg.cut(sentence)
    #     pos_list = []
    #     for w in pos_data:
    #         pos_list.append((w.word, w.flag))
    #     return pos_list

    # 句子切分
    @staticmethod
    def cut_sentence(words):
        start = 0
        i = 0
        token = 'meaningless'
        sentences = []
        punt_list = u',.!?;~，。！？；～… '
        for word in words:
            if word not in punt_list:   # 如果不是标点符号
                i += 1
                token = list(words[start:i+2]).pop()
            elif word in punt_list and token in punt_list:  # 处理省略号
                i += 1
                token = list(words[start:i+2]).pop()
            else:
                sentences.append(words[start:i+1])   # 断句
                start = i + 1
                i += 1
        if start < len(words):   # 处理最后的部分
            sentences.append(words[start:])
        return sentences

    @staticmethod
    def read_lines(filename):
        fp = open(filename, 'r')
        lines = []
        for line in fp.readlines():
            line = line.strip()
            line = line.decode("utf-8")
            lines.append(line)
        fp.close()
        return lines

    # 去除停用词
    def del_stopwords(self, seg_sent):
        new_sent = []   # 去除停用词后的句子
        for word in seg_sent:
            if word in self.stopwords:
                continue
            else:
                new_sent.append(word)
        return new_sent
