# coding:utf-8

import csv
import re
import numpy as np
import operator
import sys
import datetime
from datetime import datetime
from time import time
from rnn_theano import RNNTheano
from scipy.misc import logsumexp


vocabulary_size = 2323
unknown_token = u"\U0001f63b"
sentence_start = unicode("\0")
sentence_end = unicode("\1")

# Read the data and append start and end token
print "Reading csv file..."
sentences = []
targets = []
with open("data/comment.csv", "rb") as comment_file:
    reader = csv.DictReader(comment_file)
    for data in reader:
        comments = re.sub("\s+", "，", data['cmt'])
        comments = re.split("。|@@@", comments)
        for comment in comments:
            if len(comment.decode("utf-8")) > 3 and len(set(comment.decode("utf-8"))) > 3:
                sentences.append("%s%s%s" % (str(sentence_start), comment, str(sentence_end)))
                targets.append(data["score"])

print len(sentences)
char_map = {sentence_start: 0, sentence_end: 1}
char_array = [sentence_start, sentence_end]
index = 2
for sentence in sentences:
    for char in sentence.decode("utf-8"):
        if char not in char_map:
            char_map[char] = index
            char_array.append(char)
            index += 1
char_map[unknown_token] = index
unknown_token_index = index
char_array.append(unknown_token)


def calculate_word_expression(s):
    return [char_map.get(c, unknown_token_index) for c in s.decode("utf-8")]


def show_sentence(sentence_array):
    return "".join(str(char_array[char_index].encode("utf-8")) for char_index in sentence_array)


print show_sentence([4, 13, 10, 2322, 280])
print calculate_word_expression("质量不错")

# Create the training data
X_train = np.asarray([calculate_word_expression(sent[:-1]) for sent in sentences])
y_train = np.asarray([calculate_word_expression(sent[1:]) for sent in sentences])
# y_train = np.asarray([t for t in targets])


# def softmax(x):
#     xt = np.exp(x - np.max(x))
#     return xt / np.sum(xt)


def log_softmax(vec):
    return vec - logsumexp(vec)


def softmax(vec):
    return np.exp(log_softmax(vec))


class RNNNumpy:

    def __init__(self, word_dim, hidden_dim=128, bptt_truncate=4):
        # Assign instance variables
        self.word_dim = word_dim
        self.hidden_dim = hidden_dim
        self.bptt_truncate = bptt_truncate
        # Randomly initialize the network parameters
        self.U = np.random.uniform(-np.sqrt(1./word_dim), np.sqrt(1./word_dim), (hidden_dim, word_dim))
        self.V = np.random.uniform(-np.sqrt(1./hidden_dim), np.sqrt(1./hidden_dim), (word_dim, hidden_dim))
        self.W = np.random.uniform(-np.sqrt(1./hidden_dim), np.sqrt(1./hidden_dim), (hidden_dim, hidden_dim))

    def forward_propagation(self, x):
        # The total number of time steps
        T = len(x)
        # During forward propagation we save all hidden states in s because need them later
        # We add one additional element for the initial hidden, which we set to 0
        s = np.zeros((T + 1, self.hidden_dim))
        s[-1] = np.zeros(self.hidden_dim)
        # The outputs at each time step. Again, we save them for later.
        o = np.zeros((T, self.word_dim))
        # For each time step...
        for t in np.arange(T):
            # Note that we are indxing U by x[t]. This is the same as multiplying U with a one-hot vector.
            s[t] = np.tanh(self.U[:, x[t]] + self.W.dot(s[t - 1]))
            o[t] = softmax(self.V.dot(s[t]))
        return [o, s]

    def predict(self, x):
        # Perform forward propagation and return index of the highest score.
        o, s = self.forward_propagation(x)
        return np.argmax(o, axis=1)

    def calculate_total_loss(self, x, y):
        L = 0
        # For each sentence...
        for i in np.arange(len(y)):
            o, s = self.forward_propagation(x[i])
            # We only care about our prediction of the "correct" words
            correct_word_predictions = o[np.arange(len(y[i])), y[i]]
            # Add to the loss based on how off we were
            L += -1 * np.sum(np.log(correct_word_predictions))
        return L

    def calculate_loss(self, x, y):
        # Divide the total loss by the number of training examples
        N = np.sum((len(y_i) for y_i in y))
        return self.calculate_total_loss(x, y) / N

    def bptt(self, x, y):
        T = len(y)
        # Perform forward propagation
        o, s = self.forward_propagation(x)
        # We accumulate the gradients in these variables
        dLdU = np.zeros(self.U.shape)
        dLdV = np.zeros(self.V.shape)
        dLdW = np.zeros(self.W.shape)
        delta_o = o
        delta_o[np.arange(len(y)), y] -= 1.
        # For each output backwards...
        for t in np.arange(T)[::-1]:
            dLdV += np.outer(delta_o[t], s[t].T)
            # Initial delta calculation
            delta_t = self.V.T.dot(delta_o[t]) * (1 - (s[t] ** 2))
            # Backpropagation through time (for at most self.bptt_truncate steps)
            for bptt_step in np.arange(max(0, t - self.bptt_truncate), t + 1)[::-1]:
                # print "Backpropagation step t=%d bptt step=%d " % (t, bptt_step)
                dLdW += np.outer(delta_t, s[bptt_step - 1])
                dLdU[:, x[bptt_step]] += delta_t
                # Update delta for next step
                delta_t = self.W.T.dot(delta_t) * (1 - s[bptt_step - 1] ** 2)
        return [dLdU, dLdV, dLdW]

    def gradient_check(self, x, y, h=0.001, error_threshold=0.01):
        # Calculate the gradients using backpropagation. We want to checker if these are correct.
        bptt_gradients = self.bptt(x, y)
        # List of all parameters we want to check.
        model_parameters = ['U', 'V', 'W']
        # Gradient check for each parameter
        for pidx, pname in enumerate(model_parameters):
            # Get the actual parameter value from the mode, e.g. model.W
            parameter = operator.attrgetter(pname)(self)
            print "Performing gradient check for parameter %s with size %d." % (pname, np.prod(parameter.shape))
            # Iterate over each element of the parameter matrix, e.g. (0,0), (0,1), ...
            it = np.nditer(parameter, flags=['multi_index'], op_flags=['readwrite'])
            while not it.finished:
                ix = it.multi_index
                # Save the original value so we can reset it later
                original_value = parameter[ix]
                # Estimate the gradient using (f(x+h) - f(x-h))/(2*h)
                parameter[ix] = original_value + h
                gradplus = self.calculate_total_loss([x], [y])
                parameter[ix] = original_value - h
                gradminus = self.calculate_total_loss([x], [y])
                estimated_gradient = (gradplus - gradminus) / (2 * h)
                # Reset parameter to original value
                parameter[ix] = original_value
                # The gradient for this parameter calculated using backpropagation
                backprop_gradient = bptt_gradients[pidx][ix]
                # calculate The relative error: (|x - y|/(|x| + |y|))
                relative_error = np.abs(backprop_gradient - estimated_gradient) / (np.abs(backprop_gradient) + np.abs(estimated_gradient))
                # If the error is to large fail the gradient check
                if relative_error > error_threshold:
                    print "Gradient Check ERROR: parameter=%s ix=%s" % (pname, ix)
                    print "+h Loss: %f" % gradplus
                    print "-h Loss: %f" % gradminus
                    print "Estimated_gradient: %f" % estimated_gradient
                    print "Backpropagation gradient: %f" % backprop_gradient
                    print "Relative Error: %f" % relative_error
                    return
                it.iternext()
            print "Gradient check for parameter %s passed." % pname

    # Performs one step of SGD.
    def sgd_step(self, x, y, learning_rate):
        # Calculate the gradients
        dLdU, dLdV, dLdW = self.bptt(x, y)
        # Change parameters according to gradients and learning rate
        self.U -= learning_rate * dLdU
        self.V -= learning_rate * dLdV
        self.W -= learning_rate * dLdW


# Outer SGD Loop
# - model: The RNN model instance
# - X_train: The training data set
# - y_train: The training data labels
# - learning_rate: Initial learning rate for SGD
# - nepoch: Number of times to iterate through the complete dataset
# - evaluate_loss_after: Evaluate the loss after this many epochs
def train_with_sgd(model, X_train, y_train, learning_rate=0.005, nepoch=100, evaluate_loss_after=5):
    # We keep track of the losses so we can plot them later
    losses = []
    num_examples_seen = 0
    for epoch in range(nepoch):
        # Optionally evaluate the loss
        if epoch % evaluate_loss_after == 0:
            loss = model.calculate_loss(X_train, y_train)
            losses.append((num_examples_seen, loss))
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print "%s: Loss after num_examples_seen=%d epoch=%d: %f" % (time, num_examples_seen, epoch, loss)
            # Adjust the learning rate if loss increases
            if len(losses) > 1 and losses[-1][1] > losses[-2][1]:
                learning_rate *= 0.5
                print "Setting learning rate to %f" % learning_rate
            sys.stdout.flush()
        # For each training example...
        for i in range(len(y_train)):
            # One SGD step
            model.sgd_step(X_train[i], y_train[i], learning_rate)
            num_examples_seen += 1


def save_model_parameters_theano(outfile, model):
    U, V, W = model.U.get_value(), model.V.get_value(), model.W.get_value()
    np.savez(outfile, U=U, V=V, W=W)
    print "Saved model parameters to %s." % outfile


def load_model_parameters_theano(path, model):
    npzfile = np.load(path)
    U, V, W = npzfile["U"], npzfile["V"], npzfile["W"]
    model.hidden_dim = U.shape[0]
    model.word_dim = U.shape[1]
    model.U.set_value(U)
    model.V.set_value(V)
    model.W.set_value(W)
    print "Loaded model parameters from %s. hidden_dim=%d word_dim=%d" % (path, U.shape[0], U.shape[1])

np.random.seed(10)
model = RNNNumpy(vocabulary_size)
o, s = model.forward_propagation(X_train[10])
print show_sentence(X_train[10])
print o.shape
print o

predictions = model.predict(X_train[10])
print predictions.shape
print predictions
print show_sentence(predictions)

# Limit to 1000 examples to save time
print "Expected Loss for random predictions: %f" % np.log(vocabulary_size)
print "Actual loss: %f" % model.calculate_loss(X_train[:1000], y_train[:1000])

# To avoid performing millions of expensive calculations we use a smaller vocabulary size for checking.
grad_check_vocab_size = 100
np.random.seed(10)
model = RNNNumpy(grad_check_vocab_size, 10, bptt_truncate=1000)
model.gradient_check([0, 1, 2, 3], [1, 2, 3, 4])

np.random.seed(10)
model = RNNNumpy(vocabulary_size)
t0 = time()
model.sgd_step(X_train[10], y_train[10], 0.005)
print time() - t0

np.random.seed(10)
# Train on a small subset of the data to see what happens
model = RNNTheano(vocabulary_size)
# load_model_parameters_theano("model.data", model)
# train_with_sgd(model, X_train, y_train, nepoch=100, evaluate_loss_after=10)
# model = RNNNumpy(vocabulary_size)
train_with_sgd(model, X_train, y_train, nepoch=10, evaluate_loss_after=1)
# train_with_sgd(model, X_train[:100], y_train[:100], nepoch=10, evaluate_loss_after=1)
# with open("model.data", "w") as out_file:
#     save_model_parameters_theano(out_file, model)


def generate_sentence(model):
    # We start the sentence with the start token
    new_sentence = [char_map[sentence_start]]
    # Repeat until we get an end token
    while not new_sentence[-1] == char_map[sentence_end]:
        next_word_probs = model.forward_propagation(new_sentence)
        sampled_word = char_map[unknown_token]
        # We don't want to sample unknown words
        while sampled_word == char_map[unknown_token]:
            try:
                samples = np.random.multinomial(1, next_word_probs[-1])
                sampled_word = np.argmax(samples)
            except:
                return ""
        new_sentence.append(sampled_word)
    return show_sentence(new_sentence[1:-1])


num_sentences = 100
senten_min_length = 9

for i in range(num_sentences):
    sent = []
    # We want long sentences, not sentences with one or two words
    while len(sent) < senten_min_length:
        sent = generate_sentence(model)
    print "".join(sent)