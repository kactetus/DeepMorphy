import os
import yaml
import pickle
import logging
from collections import defaultdict

class MyDefaultDict(defaultdict):
    def __missing__(self, key):

        if self.default_factory is None:
            raise KeyError( key )
        else:
            ret = self[key] = self.default_factory(key)
            return ret

__config__ = None

def config():
    global __config__

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%d.%m.%Y %H:%M:%S'
    )
    if __config__ is None:
        with open('config.yml', 'r') as f:
            __config__ = yaml.load(f)

        classes_path = os.path.join(__config__['dataset_path'], f"classification_classes.pkl")
        if os.path.exists(classes_path):
            with open(classes_path, 'rb') as f:
                __config__['main_classes'] = pickle.load(f)
                __config__['main_classes_count'] = len(__config__['main_classes'])

    return __config__


def get_flat_words(words):
    for item in words:
        lemma = item['lemma']
        lemma['lemma'] = lemma['text']
        lemma['id'] = item['id']
        for form in item['forms']:
            word = dict(lemma)
            for key in form:
                word[key] = form[key]

            yield word


def get_grams_info(config):
    dict_post_types = config['dict_post_types']
    grammemes_types = config['grammemes_types']
    src_convert = {}
    classes_indexes = {}

    for gram_key in grammemes_types:
        gram = grammemes_types[gram_key]
        cls_dic = gram['classes']
        classes_indexes[gram_key] = {}
        for cls_key in cls_dic:
            cls_obj = cls_dic[cls_key]
            classes_indexes[gram_key][cls_key] = cls_obj['index']

            for key in cls_obj['keys']:
                src_convert[key.lower()] = (gram_key, cls_key)

    for post_key in dict_post_types:
        cls_obj = dict_post_types[post_key.lower()]
        p_key = ('post', post_key.lower())
        for key in cls_obj['keys']:
            src_convert[key.lower()] = p_key

    return src_convert, classes_indexes


def decode_word(vect_mas):
    conf = config()

    word = []
    for ci in vect_mas:
        if ci == conf['end_token']:
            return "".join(word)
        elif ci < len((conf['chars'])):
            word.append(conf['chars'][ci])
        else:
            word.append("0")

    return "".join(word)