import datetime
import getopt
import os
import sys
import time

from classification_keras import gen_model, generate_more_data
from scraping_selenium import begin_scrap


def print_debug(start_time, str_to_print):
    print('--- ' + str(datetime.timedelta(seconds=(time.time() - start_time))) + ' --- ' + str_to_print + ' ---')
    with open("_timer.txt", "a+") as timer_file:
        print("--- {} --- {} ---"
              .format(datetime.timedelta(seconds=(time.time() - start_time)), str_to_print),
              file=timer_file)


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
    print_debug(start_time, 'step scrap images')

    path_dataset = 'flowers/'
    path_datascrapped = 'data/'
    nb_img_d = 4326  # initialisation avec le nombre d'image du dataset
    # Boucle pour doubler le nombre d'images 2 fois
    for j in range(3):
        if j > 0:
            nb_img_s = double_data(path_datascrapped)
            nb_img_d = double_data(path_dataset)
            print_debug(start_time, 'to double data')
        nb = 5
        for i in range(7):
            name = 'scrapped_epoch-' + str(nb) + '_size-64_images-' + str(nb_img_s)
            gen_model(name, path_datascrapped, 64, nb, len(targets))
            nb *= 2
            print_debug(start_time, name)

        nb = 5
        for i in range(7):
            name = 'scrapped_epoch-' + str(nb) + '_size-128_images-' + str(nb_img_s)
            gen_model(name, path_datascrapped, 128, nb, len(targets))
            nb *= 2
            print_debug(start_time, name)

        nb = 5
        for i in range(7):
            name = 'dataset_epoch-' + str(nb) + '_size-64_images-' + str(nb_img_d)
            gen_model(name, path_dataset, 64, nb, len(targets))
            nb *= 2
            print_debug(start_time, name)

        nb = 5
        for i in range(7):
            name = 'dataset_epoch-' + str(nb) + '_size-128_images-' + str(nb_img_d)
            gen_model(name, path_dataset, 128, nb, len(targets))
            nb *= 2
            print_debug(start_time, name)


if __name__ == '__main__':
    main(sys.argv[1:])
