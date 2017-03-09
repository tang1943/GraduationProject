# coding=utf-8
import random

import numpy as np
import json
import pandas as pd
import codecs
import os
import pickle


class Data:
    save_dir = None
    dict_complete = False
    data_complete = False

    class2Id = {}
    id2Class = {}
    word2Id = {}
    id2Word = {}

    test_input_data = []
    test_label_data = []
    train_input_data = []
    train_label_data = []
    valid_input_data = []
    valid_label_data = []

    def __init__(self, input_path, out_path="../data/lstm_data/douban_movie3/"):
        self.save_dir = out_path
        self.dict_complete = self.load_dict()
        self.data_complete = self.load_data()
        if not self.dict_complete or not self.data_complete:
            input_data = []
            label_data = []
            data_frame = pd.read_csv(input_path, encoding="utf-8")
            for _, row in data_frame.iterrows():
                try:
                    data_, label = self.line_mapping(row["content"], int(row["score"]))
                    if data_ is not None:
                        input_data.append(data_)
                        label_data.append(label)
                except Exception, e:
                    print e
            label_data = self.get_labels_vector(label_data)
            self.get_train_valid_test_data(input_data, label_data)
            self.save_dict()

    def line_mapping(self, cmt, score):
        if 1 < score < 5:
            return
        data_array = []
        if self.dict_complete:
            class_id = self.class2Id[score]
            for word in cmt.lower():
                data_array.append(self.word2Id[word])
        else:
            class_id = self.class2Id.get(score, len(self.class2Id))
            self.class2Id[score] = class_id
            self.id2Class[class_id] = score
            try:
                for word in cmt.lower():
                    word_id = self.word2Id.get(word, len(self.word2Id))
                    self.word2Id[word] = word_id
                    self.id2Word[word_id] = word
                    data_array.append(word_id)
            except Exception, e:
                print e
        return data_array, class_id

    def get_labels_vector(self, labels):
        class_num = len(self.class2Id)
        label_array = []
        for label_id in labels:
            label_vector = np.zeros(class_num)
            label_vector[label_id] = 1
            label_array.append(label_vector)
        return label_array

    @staticmethod
    def save_dict_file(hm, out_path):
        if isinstance(hm, dict):
            of = codecs.open(out_path, 'w', encoding='utf8')
            out = json.dumps(hm, indent=4, ensure_ascii=False)
            of.write(out)
            of.close()

    @staticmethod
    def load_dict_file(input_path):
        dict_file = codecs.open(input_path, "r", "utf8")
        return json.load(dict_file)

    def save_dict(self):
        if self.save_dir is not None:
            print self.save_dir
            self.save_dict_file(self.word2Id, self.save_dir + "dataDict/word2Id")
            self.save_dict_file(self.id2Word, self.save_dir + "dataDict/id2Word")
            self.save_dict_file(self.class2Id, self.save_dir + "dataDict/class2Id")
            self.save_dict_file(self.id2Class, self.save_dir + "dataDict/id2Class")

    def load_dict(self):
        try:
            if os.path.isfile(self.save_dir + "dataDict/word2Id") and \
               os.path.isfile(self.save_dir + "dataDict/id2Word") and \
               os.path.isfile(self.save_dir + "dataDict/class2Id") and \
               os.path.isfile(self.save_dir + "dataDict/id2Class"):
                self.word2Id = self.load_dict_file(self.save_dir + "dataDict/word2Id")
                self.id2Word = self.load_dict_file(self.save_dir + "dataDict/id2Word")
                self.class2Id = self.load_dict_file(self.save_dir + "dataDict/class2Id")
                self.id2Class = self.load_dict_file(self.save_dir + "dataDict/id2Class")
                return True
        except Exception, ex:
            print ex
            return False
        return False

    def load_data(self):
        try:
            if os.path.isfile(self.save_dir + "train_data/train_data") and \
               os.path.isfile(self.save_dir + "train_data/train_labels") and \
               os.path.isfile(self.save_dir + "train_data/test_data") and \
               os.path.isfile(self.save_dir + "train_data/test_labels") and \
               os.path.isfile(self.save_dir + "train_data/valid_data") and \
               os.path.isfile(self.save_dir + "train_data/valid_labels"):
                self.train_input_data = pickle.load(open(self.save_dir + "train_data/train_data", "r"))
                self.train_label_data = pickle.load(open(self.save_dir + "train_data/train_labels", "r"))
                self.test_input_data = pickle.load(open(self.save_dir + "train_data/test_data", "r"))
                self.test_label_data = pickle.load(open(self.save_dir + "train_data/test_labels", "r"))
                self.valid_input_data = pickle.load(open(self.save_dir + "train_data/valid_data", "r"))
                self.valid_label_data = pickle.load(open(self.save_dir + "train_data/valid_labels", "r"))
                return True
        except Exception, ex:
            print ex
            return False
        return False

    def get_train_valid_test_data(self, input_data, label_data):
        self.train_input_data = []
        self.train_label_data = []
        self.test_input_data = []
        self.test_label_data = []
        self.valid_input_data = []
        self.valid_label_data = []

        for i in range(0, len(input_data)):
            rand = random.random()

            if rand <= 0.7:
                self.train_input_data.append(input_data[i])
                self.train_label_data.append(label_data[i])
            else:
                if rand < 0.99:
                    self.test_input_data.append(input_data[i])
                    self.test_label_data.append(label_data[i])
                else:
                    self.valid_input_data.append(input_data[i])
                    self.valid_label_data.append(label_data[i])
        pickle.dump(self.train_input_data, open(self.save_dir + "train_data/train_data", "w"), 2)
        pickle.dump(self.train_label_data, open(self.save_dir + "train_data/train_labels", "w"), 2)
        pickle.dump(self.test_input_data, open(self.save_dir + "train_data/test_data", "w"), 2)
        pickle.dump(self.test_label_data, open(self.save_dir + "train_data/test_labels", "w"), 2)
        pickle.dump(self.valid_input_data, open(self.save_dir + "train_data/valid_data", "w"), 2)
        pickle.dump(self.valid_label_data, open(self.save_dir + "train_data/valid_labels", "w"), 2)

    def show_sentence(self, sentence_array):
        return "".join(str(self.id2Word[str(char_index)].encode("utf-8")) for char_index in sentence_array)

    def get_class_by_id(self, class_id):
        return self.id2Class[str(class_id)]
