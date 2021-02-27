""" Generate prompt for SAT type analogy dataset """
import argparse
import json
import os
import shutil
import logging
from glob import glob
from itertools import chain, product
import bertprompt


def get_options():
    parser = argparse.ArgumentParser(description='Generate prompt for SAT type analogy dataset')
    parser.add_argument('-t', '--transformers-model',
                        help='Language model alias from transformers model hub', required=True, type=str)
    parser.add_argument('--n-blank', help='The number of intermediate blank', default='2,3,4', type=str)
    parser.add_argument('--n-blank-b', help='The number of beginning blank', default='0,1,2', type=str)
    parser.add_argument('--n-blank-e', help='The number of last blank', default='0,1,2', type=str)
    parser.add_argument('-d', '--data', help='Data name: sat/u2/u4/google/bats', default='bats', type=str)
    parser.add_argument('-r', '--revision', help='The number of revision by language model', default=100, type=int)
    parser.add_argument('-l', '--length', help='Max length of language model', default=32, type=int)
    parser.add_argument('-b', '--batch', help='Batch size', default=512, type=int)
    parser.add_argument('-k', '--topk', help='Filter to top k token prediction', default=10, type=int)
    parser.add_argument('-o', '--output-dir', help='Directory to output', default='./prompts/analogy', type=str)
    parser.add_argument('--max-data-size', help='Max data size in single run', default=2000, type=int)
    parser.add_argument('--debug', help='Show debug log', action='store_true')
    return parser.parse_args()


def main():
    opt = get_options()
    level = logging.DEBUG if opt.debug else logging.INFO
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=level, datefmt='%Y-%m-%d %H:%M:%S')
    prompter = bertprompt.Prompter(opt.transformers_model, opt.length)

    # aggregate data
    n_blank_list = [int(i) for i in opt.n_blank.split(',')]
    n_blank_b_list = [int(i) for i in opt.n_blank_b.split(',')]
    n_blank_e_list = [int(i) for i in opt.n_blank_e.split(',')]
    val, test = bertprompt.get_analogy_data(opt.data)
    word_pairs = list(chain(*[[i['stem']] + i['choice'] for i in val]))
    word_pairs += list(chain(*[[i['stem']] + i['choice'] for i in test]))
    word_pairs += [[p[1], p[0]] for p in word_pairs]
    # drop duplicated pair
    word_pairs = [i.split('||') for i in sorted({'||'.join(i) for i in word_pairs})]
    all_config = list(product(n_blank_list, n_blank_b_list, n_blank_e_list))

    # language model inference
    logging.info('GENERATE PROMPT FOR ANALOGY')
    logging.info('\t * data     : {} ({} pairs)'.format(opt.data, len(word_pairs)))
    logging.info('\t * model    : {}'.format(opt.transformers_model))
    logging.info('\t * blank    : {}'.format(n_blank_list))
    logging.info('\t * blank (b): {}'.format(n_blank_b_list))
    logging.info('\t * blank (e): {}'.format(n_blank_e_list))

    for i, (n_blank, n_blank_b, n_blank_e) in enumerate(all_config):
        logging.info('EXPERIMENT {}/{}: blank: {}, blank_b: {}, blank_e: {}'.format(
            i + 1, len(all_config), n_blank, n_blank_b, n_blank_e))
        filename = '{0}/{1}/prompt/prompt_dict.{1}.{2}.{3}.{4}.{5}.{6}.json'.format(
            opt.output_dir, opt.data, opt.transformers_model, opt.topk, n_blank, n_blank_b, n_blank_e)
        if os.path.exists(filename):
            logging.info('skip as the output found at: {}'.format(filename))
            continue
        output_dict = {}
        total_range = range(0, len(word_pairs), opt.max_data_size)
        for n_, n in enumerate(total_range):
            end = min(n + opt.max_data_size, len(word_pairs))
            logging.info('sub-experiment {}/{} ({}:{})'.format(n_, len(total_range), n, end))
            filename_ = filename.replace('.json', '.sub.{}.{}.json'.format(n_, opt.max_data_size))
            if os.path.exists(filename_):
                logging.info('\t * loading cache')
                with open(filename_, 'r') as f:
                    output_dict_tmp = json.load(f)
            else:
                word_pairs_sub = word_pairs[n:end]
                output_list_tmp = prompter.generate(
                    word_pairs_sub,
                    n_blank=n_blank,
                    n_blank_b=n_blank_b,
                    n_blank_e=n_blank_e,
                    batch_size=opt.batch,
                    topk=opt.topk,
                    n_revision=opt.revision)
                with open(filename_, 'w') as f:
                    json.dump(output_dict_tmp, f)
            output_dict.update(output_dict_tmp)

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logging.info('experiment finished, exporting result to {}'.format(filename))
        with open(filename, 'w') as f:
            json.dump(output_dict, f)
        with open(filename.replace('.json', '.top.json'), 'w') as f:
            json.dump({k: [v[0][-1], v[1][-1]] for k, v in output_dict.items()}, f)
        logging.info('deleting cached files')
        for p in glob('{0}/{1}/prompt/prompt_dict.*.sub.*.json'.format(opt.output_dir, opt.data)):
            shutil.rmtree(p)


if __name__ == '__main__':
    main()
