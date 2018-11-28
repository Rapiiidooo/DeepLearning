import time
import datetime

from classification_keras import gen_model, generate_more_data
from scraping_selenium import begin_scrap


def main():
    start_time = time.time()

    targets = [
        'Daisy flower',  # 'Fleur Marguerite',
        'Dandelion flower',  # 'Fleur Pissenlit ',
        'Rose flower',  # 'Fleur Rose',
        'Sunflower flower',  # 'Fleur Tournesol',
        'Tulip flower',  # 'Fleur Tulipe'
    ]

    for i, key in enumerate(targets):
        targets[i] = begin_scrap(key, 'bad', 'Chrome') + '.done/'

    print('--- ' + str(datetime.timedelta(seconds=(time.time() - start_time))) + ' --- to scrap images ---')

    generate_more_data('data/', 20)
    print('--- ' + str(datetime.timedelta(seconds=(time.time() - start_time))) + ' --- to multiply by 20 datas ---')

    nb = 10
    for i in range(3):
        nb *= 5
        gen_model('model_from_scrapped_' + str(nb), 'data/', 64, nb, len(targets))

    nb = 10
    for i in range(5):
        nb *= 5
        gen_model('model_from_scrapped_' + str(nb), 'data/', 128, nb, len(targets))

    print('--- ' +
          str(datetime.timedelta(seconds=(time.time() - start_time))) +
          ' --- to train all model from scrapped ---')

    generate_more_data('flowers/', 20)
    print('--- ' + str(datetime.timedelta(seconds=(time.time() - start_time))) + ' --- to multiply by 20 datas ---')

    nb = 10
    for i in range(5):
        nb *= 5
        gen_model('model_from_dataset_' + str(nb), 'flowers/', 64, nb, len(targets))

    nb = 10
    for i in range(5):
        nb *= 5
        gen_model('model_from_dataset_' + str(nb), 'flowers/', 128, nb, len(targets))

    print('--- ' +
          str(datetime.timedelta(seconds=(time.time() - start_time))) +
          ' --- to train all model from dataset ---')


if __name__ == '__main__':
    main()
