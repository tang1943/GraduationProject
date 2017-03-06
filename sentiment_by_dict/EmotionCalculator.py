# coding:utf-8
import io
from JieBa import JieBa


class EmotionCalculator:

    pos_dict = None
    neg_dict = None
    most_dict = None
    very_dict = None
    more_dict = None
    a_little_dict = None
    insufficient_dict = None
    inverse_dict = None
    jieba = None

    def __init__(self):
        # 读取情感词典
        self.pos_dict = self.__read_dict("../dict/pos_dict.txt")
        self.neg_dict = self.__read_dict("../dict/neg_dict.txt")
        self.most_dict = self.__read_dict('../dict/most.txt')  # 权值为2
        self.very_dict = self.__read_dict('../dict/very.txt')  # 权值为1.5
        self.more_dict = self.__read_dict('../dict/more.txt')  # 权值为1.25
        self.a_little_dict = self.__read_dict('../dict/a_little.txt')  # 权值为0.5
        self.insufficient_dict = self.__read_dict('../dict/insufficiently.txt')  # 权值为0.25
        self.inverse_dict = self.__read_dict('../dict/inverse.txt')  # 权值为-1
        self.jieba = JieBa()

    # 程度副词处理，根据程度副词的种类不同乘以不同的权值
    def match(self, word):
        weight = 1
        is_degree = True
        if word in self.most_dict:
            weight = 2.0
        elif word in self.very_dict:
            weight = 1.75
        elif word in self.more_dict:
            weight = 1.5
        elif word in self.a_little_dict:
            weight = 1.2
        elif word in self.insufficient_dict:
            weight = 0.5
        elif word in self.inverse_dict:
            is_degree = False
            weight = -1
        return weight, is_degree

    # 求语句的情感倾向总得分
    def sentence_sentiment_score_calculate(self, paragraph):
        # 分别记录积极情感总得分和消极情感总得分
        total_score = 0.0
        # 切分句子
        sentences = self.jieba.cut_sentence(paragraph)
        for sentence in sentences:
            # 分词
            seg_sent = self.jieba.segmentation(sentence)
            seg_sent = self.jieba.del_stopwords(seg_sent)
            last_emotion_word_index = 0
            pre_emotion_value = 0
            for current_index, word in enumerate(seg_sent):  # 逐词分析
                word_score = 0
                if word in self.pos_dict:  # 如果是积极情感词
                    word_score = 1
                    last_is_degree = False
                    for word_pre in seg_sent[last_emotion_word_index:current_index][::-1]:
                        w, is_degree = self.match(word_pre)
                        if not is_degree and last_is_degree:
                            word_score *= 0.5
                        else:
                            word_score *= w
                        last_is_degree = is_degree
                    _, is_degree = self.match(seg_sent[last_emotion_word_index])
                    if not is_degree:
                        total_score -= pre_emotion_value
                    last_emotion_word_index = current_index
                    pre_emotion_value = word_score
                elif word in self.neg_dict:  # 如果是消极情感词
                    word_score = -1
                    last_is_degree = False
                    for word_pre in seg_sent[last_emotion_word_index:current_index][::-1]:
                        w, is_degree = self.match(word_pre)
                        if not is_degree and last_is_degree:
                            word_score *= 0.5
                        else:
                            word_score *= w
                        last_is_degree = is_degree
                    _, is_degree = self.match(seg_sent[last_emotion_word_index])
                    if not is_degree:
                        total_score -= pre_emotion_value
                    last_emotion_word_index = current_index
                    pre_emotion_value = word_score
                # 如果是感叹号，表示已经到本句句尾
                elif u"！" in word or u"!" in word:
                    word_score = pre_emotion_value
                total_score += word_score
        # 该条微博情感的最终得分
        return round(total_score, 1)

    # 按行读取文件
    @staticmethod
    def __read_dict(path):
        lines = []
        for line in io.open(path, encoding="utf-8"):
            line = line.strip()
            if line != "":
                lines.append(line)
        return lines


if __name__ == "__main__":
    cal = EmotionCalculator()
    # 测试
    # test_sent = u"这手机的画面挺好，操作也比较流畅。不过拍照真的太烂了！系统也不好。"
    # test_sent = u"我不能放弃.."
    test_sent = u"嗨起来"
    # test_sent = u"华三秋招研究生统一11k  春招提高到13  14k的可能性不大"
    score = cal.sentence_sentiment_score_calculate(test_sent)
    print score
