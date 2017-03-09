# coding: utf-8
import time

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
import Data


class RNN:
    inputs = tf.placeholder(dtype=tf.int32, shape=[None, None], name="inputs")
    outs = tf.placeholder(dtype=tf.float32, shape=[None, None], name="outs")
    keep_prob = tf.placeholder(dtype=tf.float32, name="keep_prob")
    learning_rate = tf.placeholder(dtype=tf.float32, name="learning_rate")
    sess = tf.Session()

    _loss = None
    _minimize_loss = None
    _predict = None
    _correct_prediction = None
    _rate = None

    def __init__(self, vocab_size=4, word_dimension=32, class_num=2, unit_num=128, layer_num=4):
        self.vocab_size = vocab_size
        self.word_dimension = word_dimension
        self.class_num = class_num
        self.unit_num = unit_num
        self.layer_num = layer_num
        with tf.name_scope('word_embedding'):
            word_embedding = tf.get_variable(name="word_embedding",
                                             dtype=tf.float32,
                                             shape=[self.vocab_size, self.word_dimension])
            tf.summary.histogram('word_embedding', word_embedding)
        with tf.name_scope("look_up"):
            look_up = tf.nn.embedding_lookup(name="look_up", params=word_embedding, ids=self.inputs)
            tf.summary.histogram("look_up", look_up)

        with tf.name_scope("rnn_unit"):
            cell = tf.contrib.rnn.core_rnn_cell.GRUCell(self.unit_num)  # , state_is_tuple=True)
            cell = tf.contrib.rnn.core_rnn_cell.DropoutWrapper(cell=cell, input_keep_prob=self.keep_prob)
            if self.layer_num > 1:
                cell = tf.contrib.rnn.core_rnn_cell.MultiRNNCell([cell] * self.layer_num, state_is_tuple=True)

        with tf.name_scope("rnn"):
            outs, states = tf.nn.dynamic_rnn(cell=cell, inputs=look_up, dtype=tf.float32)

        # 从不同长度抓取特
        with tf.name_scope("sss"):
            filters = tf.get_variable("filters", shape=[1, self.unit_num, self.unit_num],
                                      dtype=tf.float32,
                                      initializer=tf.random_uniform_initializer(-0.1, 0.1, seed=116))
            weights = tf.nn.conv1d(outs, filters=filters, stride=1, padding="SAME")
            weights = tf.nn.softmax(weights, dim=1)
            outs = tf.reduce_sum(outs * weights, axis=1)

        outs = tf.nn.dropout(outs, keep_prob=self.keep_prob, name="dropout")
        with tf.name_scope('h2y_weights'):
            h2y_weights = tf.Variable(tf.truncated_normal([self.unit_num, self.class_num],
                                                          stddev=0.1,
                                                          seed=10,
                                                          dtype=tf.float32))
            tf.summary.histogram("h2y_weights", h2y_weights)

        with tf.name_scope('h2y_weights'):
            h2y_biases = tf.get_variable(name="h2y_biases",
                                         shape=[self.class_num],
                                         dtype=tf.float32)
            tf.summary.histogram("h2y_biases", h2y_biases)

        self.merged = tf.summary.merge_all()

        with tf.name_scope('predicts'):
            self.__outs = tf.matmul(outs, h2y_weights) + h2y_biases

    def train(self):
        _predict = self.__outs
        tf.argmax(self.__outs, 1)
        tf.argmax(self.outs, 1)
        self._rate = tf.reduce_sum(tf.cast(tf.equal(tf.argmax(self.__outs, axis=1), tf.argmax(self.outs, axis=1)), "float32"))

        with tf.name_scope('loss_train'):
            # 确认正确
            _loss = tf.reduce_sum(tf.nn.softmax_cross_entropy_with_logits(logits=_predict, labels=self.outs))
            tf.summary.scalar("loss_train", _loss)

        alg = tf.train.AdagradOptimizer(learning_rate=self.learning_rate)
        _minimize_loss = alg.minimize(loss=_loss, name="minimize_loss")

        self._loss = _loss
        self._minimize_loss = _minimize_loss
        self._predict = _predict

        return _loss, _minimize_loss, _predict

    def predict(self, fed_dict):
        fed_dict[self.keep_prob] = 1.0
        __predicts = self.sess.run(self.__outs, feed_dict=fed_dict)
        return __predicts

    def evaluate(self):
        pass

    def load_model(self):
        # noinspection PyBroadException
        try:
            tf.train.Saver().restore(self.sess, "../model/lstm_douban_movie2/model.sd")
        except Exception, ex:
            print ex
            self.sess.run(tf.global_variables_initializer())

    def save_model(self):
        saver = tf.train.Saver()
        saver_def = saver.as_saver_def()
        print saver_def.filename_tensor_name
        print saver_def.restore_op_name

        saver.save(self.sess, "../model/lstm_douban_movie2/model.sd")
        tf.train.write_graph(self.sess.graph_def, "../model/lstm_douban_movie2", "model.proto", as_text=False)
        tf.train.write_graph(self.sess.graph_def, "../model/lstm_douban_movie2", "model.txt", as_text=True)

    def train_writer(self):
        return tf.summary.FileWriter('../log/douban_movie2', self.sess.graph)

    def train_min_data(self, min_inputs_set, min_labels_set, keep_prob=0.4, learning_rate=0.08):
        loss_total = 0
        right_count = 0
        for key in min_labels_set:
            _, loss = self.sess.run([self._minimize_loss, self._loss],
                                    feed_dict={
                                        self.inputs: min_inputs_set[key],
                                        self.outs: min_labels_set[key],
                                        self.keep_prob: keep_prob,
                                        self.learning_rate: learning_rate
                                    })

            right_count += self.sess.run(self._rate, feed_dict={
                              self.inputs: min_inputs_set[key],
                              self.outs: min_labels_set[key],
                              self.keep_prob: 1.0
                          })
            loss_total += loss
        return loss_total, right_count

    def test_min_data(self, min_inputs_set, min_labels_set):
        global data
        loss_total = 0
        confusion_matrix = np.zeros((self.class_num, self.class_num))
        right_count = 0
        with open("../log/error_douban2.list", "w") as error_output:
            for key in min_labels_set:
                input_data = min_inputs_set[key]
                input_label = min_labels_set[key]
                predicts, loss = self.sess.run([self._predict, self._loss],
                                               feed_dict={self.inputs: input_data,
                                                          self.outs: input_label,
                                                          self.keep_prob: 1.0})
                loss_total += loss
                predict_id = np.argmax(predicts, 1)
                target_id = np.argmax(input_label, 1)
                for index, pair in enumerate(zip(target_id, predict_id)):
                    t = pair[0]
                    p = pair[1]
                    if t == p:
                        right_count += 1
                    else:
                        error_output.write("%s,%d-->%d\n" % (data.show_sentence(input_data[index]),
                                                             data.get_class_by_id(t),
                                                             data.get_class_by_id(p)))
                    confusion_matrix[t][p] += 1
            return confusion_matrix, loss_total, right_count


data = None


def train_model():
    global data
    data = Data.Data("../data/db_comment/movie_comments.csv")
    train_inputs = data.train_input_data
    train_labels = data.train_label_data
    test_inputs = data.test_input_data
    test_labels = data.test_label_data
    valid_inputs = data.valid_input_data
    valid_labels = data.valid_label_data

    print len(valid_labels)
    print len(valid_inputs)

    batch_size = 50000
    train_data_length = len(train_labels)
    indexes = np.arange(train_data_length)

    valid_length = len(valid_labels)
    test_length = len(test_labels)

    rnn_obj = RNN(vocab_size=len(data.id2Word), class_num=len(data.class2Id))

    rnn_obj.train()

    # train_writer = rnn_obj.train_writer()
    rnn_obj.load_model()
    # rnn_obj.test_datas(test_inputs, test_labels)
    # rnn_obj.save_model()
    train_loss = []
    valid_loss = []
    train_right_rates = []
    valid_right_rates = []
    plt.ion()

    for step in range(0, 3):
        start_index = 0
        # 打乱数据顺序
        np.random.shuffle(indexes)
        while start_index < train_data_length:
            # 计算截止下标
            end_index = start_index + batch_size
            end_index = end_index if end_index < train_data_length else train_data_length
            # 分组数据
            total_word, batch_data, batch_labels = group_by_str_length(train_inputs, train_labels, indexes[start_index:end_index])
            print "-------train data------------"
            pre_time = time.time()
            loss_count, r_count = rnn_obj.train_min_data(batch_data, batch_labels)
            data_count = end_index - start_index
            loss = loss_count * 1.0 / data_count
            right_rate = r_count * 1.0 / data_count
            train_loss.append(loss)
            train_right_rates.append(right_rate)
            print "train loss:%.6f" % loss
            print "train speed:%.2f/s:" % (total_word * 1.0 / (time.time() - pre_time))
            print "train right rate:%.4f" % right_rate
            print "-------valid data------------"
            _, valid_input_set, valid_label_set = group_by_str_length(valid_inputs, valid_labels, range(valid_length))
            valid_stat_mat, valid_total_loss, valid_right_count = rnn_obj.test_min_data(valid_input_set, valid_label_set)
            valid_avg_loss = valid_total_loss / valid_length
            valid_right_rate = valid_right_count * 1.0 / valid_length
            print "valid loss:%.4f" % valid_avg_loss
            print "valid right rate:%.4f" % valid_right_rate
            print "confusion_matrix:"
            print valid_stat_mat

            valid_loss.append(valid_avg_loss)
            valid_right_rates.append(valid_right_rate)
            start_index = end_index
            # 保存模型
            rnn_obj.save_model()
            # 更新图表
            plt.plot(train_loss, 'cx-', valid_loss, 'mo:')
            plt.savefig("picture.png")
            plt.pause(0.1)
        # 一遍迭代后跑测试集
        print "-----------test_data-------------"
        _, test_input_set, test_label_set = group_by_str_length(test_inputs, test_labels, range(test_length))
        test_stat_mat, test_total_loss, test_right_count = rnn_obj.test_min_data(test_input_set, test_label_set)
        print "test loss:%.4f" % (test_total_loss * 1.0 / test_length)
        print "right rate:%.4f" % (test_right_count * 1.0 / test_length)
        print "confusion_matrix:"
        print test_stat_mat
        # 保存模型
        rnn_obj.save_model()
        # 保存验证参数
    save_array_to_file(train_loss, "train_loss.txt")
    save_array_to_file(valid_loss, "valid_loss.txt")


def save_array_to_file(arr, path):
    with open(path, "w") as f:
        for d in arr:
            f.write("%.2f\n" % d)


def group_by_str_length(input_data, input_labels, indexes):
    output_data = {}
    output_labels = {}
    total_word = 0
    for index in indexes:
        data_length = len(input_data[index])
        total_word += data_length
        d = output_data.get(data_length, [])
        d.append(input_data[index])
        output_data[data_length] = d
        l = output_labels.get(data_length, [])
        l.append(input_labels[index])
        output_labels[data_length] = l
    for key in output_labels.keys():
        length = len(output_labels[key])
        group_length = 350000 / key
        if length > group_length:
            label_data = output_labels[key]
            data_ = output_data[key]
            output_labels[key] = label_data[0:group_length]
            output_data[key] = data_[0:group_length]
            start_index = group_length
            while start_index < length:
                end_index = min(start_index + group_length, length)
                output_labels["%d(%d)" % (key, start_index)] = label_data[start_index: end_index]
                output_data["%d(%d)" % (key, start_index)] = data_[start_index: end_index]
                start_index = end_index
    return total_word, output_data, output_labels


if __name__ == '__main__':

    train_model()

