import datetime
import getopt
import os
import sys
import time

from classification_keras import gen_model, generate_more_data, get_nb_model
from scraping_selenium import begin_scrap

TIMER_FILE = "_timer.txt"


def print_time_total():
    time_list = []
    with open(TIMER_FILE, "r") as timer_file:
        for line in timer_file:
            time_list.append(line[4:11])

    sum_time = datetime.timedelta()
    for i in time_list:
        try:
            (h, m, s) = i.split(':')
            d = datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
            sum_time += d
        except:
            pass
    with open(TIMER_FILE, "a+") as timer_file:
        print("--- {} --- {} ---"
              .format(sum_time, 'Total time spend.'),
              file=timer_file)


def print_debug(start_time, str_to_print):
    print('--- ' + str(datetime.timedelta(seconds=(time.time() - start_time))) + ' --- ' + str_to_print + ' ---')
    with open(TIMER_FILE, "a+") as timer_file:
        print("--- {} --- {} ---"
              .format(datetime.timedelta(seconds=(time.time() - start_time)), str_to_print),
              file=timer_file)
    return time.time()


def double_data(path):
    return generate_more_data(path, 1)


def usage():
    print('python3 ', os.path.basename(__file__), " [\"list\" \"of\" \"argument about the\" \"categories researched\"]")


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hg:d", ["help", "grammar="])
        if len(args) < 1:
            usage()
            sys.exit(2)
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    start_time = time.time()

    targets = []
    for arg in args:
        targets.append(arg)

    nb_img_s = 0
    for i, key in enumerate(targets):
        targets[i] = begin_scrap(key, 'bad', 'Chrome')
        nb_img_s += int(targets[i])
    start_time = print_debug(start_time, 'step scrap images')

    path_dataset = 'flowers/'
    path_datascrapped = 'data/'
    nb_img_d = 4326  # initialisation avec le nombre d'image du dataset en dur pour aller plus vite

    size_list = [32, 64, 128]
    model_list = get_nb_model()

    for i in range(2):
        for model in model_list:
            for size in size_list:
                nb = 5
                while nb <= 320:
                    name = 'scrapped_epoch-' + str(nb) \
                           + '_size-' + str(size) \
                           + '_images-' + str(nb_img_s) \
                           + '_model-' + str(model)
                    if os.path.exists('model/' + name + '.h5') is False:
                        gen_model(name, path_datascrapped, size, nb, len(targets), model)
                        start_time = print_debug(start_time, name)
                    nb *= 2

            for size in size_list:
                nb = 5
                while nb <= 320:
                    name = 'dataset_epoch-' + str(nb) \
                           + '_size-' + str(size) \
                           + '_images-' + str(nb_img_d) \
                           + '_model-' + str(model)
                    if os.path.exists('model/' + name + '.h5') is False:
                        gen_model(name, path_dataset, size, nb, len(targets), model)
                        start_time = print_debug(start_time, name)
                    nb *= 2

        if i == 0:
            nb_img_s = double_data(path_datascrapped)
            nb_img_d = double_data(path_dataset)
            start_time = print_debug(start_time, 'to double data')
            size_list = [32, 64]  # memory probably will not be enought

    print_time_total()


if __name__ == '__main__':
    main(sys.argv[1:])
