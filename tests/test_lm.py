""" UnitTest """
import unittest
import logging
from pprint import pprint
from bertprompt import Prompter
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S')


class Test(unittest.TestCase):
    """ Test """

    def test(self):
        lm = Prompter('albert-base-v1', max_length=32)

        # test word pair infilling
        test_candidates = [["pleasure", "hedonist"], ["emotion", "demagogue"], ["dog", "cat"], ['vapor', 'evaporate']]
        pprint(lm.generate(word_pairs=test_candidates, n_blank=2, n_blank_b=0, n_blank_e=0, n_revision=1))

        # test sentence revision
        test_sentences = ['emotion and violence: demagogue', 'opinion of a communist sympathizer']
        vocab_to_keep = ['demagogue', 'opinion']  #
        pprint(lm.generate(seed_sentences=test_sentences, vocab_to_keep=vocab_to_keep, n_revision=2))

        # test sentence revision with mask
        test_sentences = ['One of the things you do when you are alive is [MASK].',
                          'Something that might happen while analysing something is [MASK].']
        vocab_to_keep = [['alive', '[MASK]'], ['[MASK]']]
        pprint(lm.generate(seed_sentences=test_sentences, vocab_to_keep=vocab_to_keep, n_revision=2))


if __name__ == "__main__":
    unittest.main()
