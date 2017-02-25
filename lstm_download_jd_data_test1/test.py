# -*- coding: utf-8 -*-
import tensorflow as tf


class test:
    sess = tf.Session()
    inputs = tf.placeholder(dtype=tf.int32, shape=[None, None], name="inputs")

    def __init__(self):
        self.layer_num = 3

    def save_model(self):
        saver = tf.train.Saver()
        saver_def = saver.as_saver_def()
        print saver_def.filename_tensor_name
        print saver_def.restore_op_name

        saver.save(self.sess, "./lstm_example/model.sd")
        tf.train.write_graph(self.sess.graph_def, "./lstm_example", "model.proto", as_text=False)
        tf.train.write_graph(self.sess.graph_def, "./lstm_example", "model.txt", as_text=True)

    def model(self):
        with tf.name_scope('word_embedding'):
            word_embedding = tf.get_variable(name="word_embedding",
                                             dtype=tf.float32,
                                             shape=[10, 2])
            tf.histogram_summary('word_embedding', word_embedding)

        with tf.name_scope("look_up"):
            look_up = tf.nn.embedding_lookup(name="look_up", params=word_embedding, ids=self.inputs)
            tf.histogram_summary("look_up", look_up)

        with tf.name_scope("rnn_unit"):
            cell = tf.nn.rnn_cell.GRUCell(10)  # , state_is_tuple=True)
            cell = tf.nn.rnn_cell.DropoutWrapper(cell=cell, input_keep_prob=1.0)
            if self.layer_num > 1:
                cell = tf.nn.rnn_cell.MultiRNNCell([cell] * self.layer_num, state_is_tuple=True)
        with tf.name_scope("rnn"):
            outs, states = tf.nn.dynamic_rnn(cell=cell, inputs=look_up, dtype=tf.float32)

        return outs[:,-1]

if __name__ == '__main__':
    ob=test()
    a=ob.model()
    ob.sess.run(tf.initialize_all_variables())
    c=ob.sess.run(a, feed_dict={ob.inputs:[[1,2,3]]})

    ob.save_model()
    print c