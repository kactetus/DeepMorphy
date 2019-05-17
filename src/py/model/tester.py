import os, pickle
import numpy as np
import tensorflow as tf
from tqdm import tqdm
from model import RNN
from utils import config, decode_word


class Tester:
    def __init__(self):
        self.config = config()
        self.config['graph_part_configs']['lemm']['use_cls_placeholder'] = True
        self.rnn = RNN(True)
        self.chars = {c: index for index, c in enumerate(self.config['chars'])}
        self.batch_size = 4096

    def test(self):
        config = tf.ConfigProto(allow_soft_placement=True)

        with tf.Session(config = config, graph=self.rnn.graph) as sess:
            sess.run(tf.global_variables_initializer())
            sess.run(tf.local_variables_initializer())
            latest_checkpoint = tf.train.latest_checkpoint(self.rnn.save_path)
            self.rnn.saver.restore(sess, latest_checkpoint)

            for gram in self.rnn.gram_keys:
                full_cls_acc, part_cls_acc = self.__test_classification__(sess, gram, self.rnn.gram_graph_parts[gram])
                tqdm.write(f"{gram}. Full cls acc: {full_cls_acc}; part_cls_acc: {part_cls_acc}")

            full_cls_acc, part_cls_acc = self.__test_classification__(sess, 'main', self.rnn.main_graph_part)
            tqdm.write(f"main. full_cls_acc: {full_cls_acc}; part_cls_acc: {part_cls_acc}")
            lemm_acc = self.__test_lemmas__(sess)
            tqdm.write(f"Lemma acc: {lemm_acc}")

    def __test_classification__(self, sess, key, graph_part):
        path = os.path.join(self.rnn.config['dataset_path'], f"{key}_test_dataset.pkl")
        with open(path, 'rb') as f:
            et_items = pickle.load(f)

        wi = 0
        pbar = tqdm(total=len(et_items))

        etalon = []
        results = []
        while wi < len(et_items):
            bi = 0
            xs = []
            indexes = []
            seq_lens = []
            max_len = 0

            while bi < self.batch_size and wi < len(et_items):
                word = et_items[wi]['src']
                etalon.append(et_items[wi]['y'])
                for c_index, char in enumerate(word):
                    xs.append(self.chars[char] if char in self.chars else self.chars['UNDEFINED'])
                    indexes.append([bi, c_index])
                cur_len = len(word)
                if cur_len > max_len:
                    max_len = cur_len
                seq_lens.append(cur_len)
                bi += 1
                wi += 1
                pbar.update(1)

            lnch = [graph_part.probs[0]]
            nn_results = sess.run(
                lnch,
                {
                    self.rnn.batch_size: bi,
                    self.rnn.seq_lens[0]: np.asarray(seq_lens),
                    self.rnn.x_vals[0]: np.asarray(xs),
                    self.rnn.x_inds[0]: np.asarray(indexes),
                    self.rnn.x_shape[0]: np.asarray([bi, max_len])
                }
            )
            results.extend(nn_results[0])

        total = len(etalon)
        total_classes = 0
        full_correct = 0
        part_correct = 0

        for index, et in enumerate(etalon):
            classes_count = et.sum()
            good_classes = np.argwhere(et == 1).ravel()
            rez_classes = np.argsort(results[index])[-classes_count:]

            total_classes += classes_count
            correct = True
            for cls in rez_classes:
                if cls in good_classes:
                    part_correct += 1
                else:
                    correct = False

            if correct:
                full_correct += 1

        full_acc = full_correct / total
        cls_correct = part_correct / total_classes

        return full_acc, cls_correct

    def __test_lemmas__(self, sess):
        path = os.path.join(self.config['dataset_path'], "lemma_test_dataset.pkl")
        with open(path, 'rb') as f:
            words = pickle.load(f)

        words = [
            word
            for word in words
            if all([c in self.config['chars'] for c in word['x_src']])
        ]

        words_to_parse = [
            (word['x_src'], word['main_cls'])
            for word in words
        ]

        rez_words = list(self.__infer_lemmas__(sess, words_to_parse))
        total = len(words_to_parse)
        wrong = 0
        for index, lem in enumerate(rez_words):
            et_word = words[index]
            if lem != et_word['y_src']:
                wrong += 1

        correct = total - wrong
        acc = correct / total
        return acc


    def __infer_lemmas__(self, sess, words):
        wi = 0
        pbar = tqdm(total=len(words))
        while wi < len(words):
            bi = 0
            xs = []
            clss = []
            indexes = []
            seq_lens = []
            max_len = 0

            while bi < self.batch_size and wi < len(words):
                word = words[wi][0]
                cls = words[wi][1]
                for c_index, char in enumerate(word):
                    xs.append(self.chars[char])
                    indexes.append([bi, c_index])
                cur_len = len(word)
                clss.append(cls)
                if cur_len>max_len:
                    max_len = cur_len
                seq_lens.append(cur_len)
                bi += 1
                wi += 1
                pbar.update(1)

            lnch = [self.rnn.lem_graph_part.results[0]]
            results = sess.run(
                lnch,
                {
                    self.rnn.batch_size: bi,
                    self.rnn.seq_lens[0]: np.asarray(seq_lens),
                    self.rnn.x_vals[0]: np.asarray(xs),
                    self.rnn.x_inds[0]: np.asarray(indexes),
                    self.rnn.lem_graph_part.cls[0]: np.asarray(clss),
                    self.rnn.x_shape[0]: np.asarray([bi, max_len])
                }
            )
            for word_src in results[0]:
                yield decode_word(word_src)


    def get_test_lemmas(self, words):
        with tf.Session(graph=self.rnn.graph) as sess:
            sess.run(tf.global_variables_initializer())
            sess.run(tf.local_variables_initializer())
            latest_checkpoint = tf.train.latest_checkpoint(self.rnn.save_path)
            self.rnn.saver.restore(sess, latest_checkpoint)
            return list(self.__infer_lemmas__(sess, words))


if __name__ == "__main__":
    tester = Tester()
    tester.test()