import os
import os.path
import errno
import time
import urllib.request

import magic
import progressbar
from selenium import webdriver

LIMIT = 1000


def init_progressbar(title, valmax):
    bar = progressbar.ProgressBar(maxval=valmax,
                                  widgets=[progressbar.Bar('=', title + ' [', ']'), ' ', progressbar.Percentage()])
    return bar


def scroll_until_end(driver):
    # ----------------------------
    # Region to scroll to the end
    # https://stackoverflow.com/questions/20986631/how-can-i-scroll-a-web-page-using-selenium-webdriver-in-python
    # ----------------------------
    scroll_limit_pause = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(scroll_limit_pause)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                # click sur le bouton "+ de résultat"
                driver.find_element_by_xpath('//*[@id="smb"]').click()
            except:
                break
        last_height = new_height
    # ----------------------------
    # End region
    # ----------------------------


def download_all(directory, file):
    # Bug Forbidden 403 for pexel
    # WORKARROUND depreciation AppURLopener()
    # code trouvé sur : https://code.i-harness.com/en/q/2115ba9
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent',
                          'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    # End résolution du bug

    my_mkdir(directory)
    i = 0
    num_lines = sum(1 for line in open(file))
    bar = init_progressbar(str(num_lines-1) + ' different to download ...', num_lines)
    bar.start()
    with open(file, "r+") as f:
        for ibar, line in enumerate(f):
            file_name = directory + '/' + str(i)
            while os.path.exists(file_name):
                i += 100
                file_name = file_name.replace(str(i - 100), str(i))
            try:
                urllib.request.urlretrieve(line, file_name)
            except Exception as e:
                if line.__contains__("Step Done."):
                    pass
                else:
                    print("Error: ", line)
                    print(e)
            bar.update(ibar+1)
            i += 1
        bar.finish()
    # section rename files with right extension
    files = os.listdir(directory)
    nb_files = len(files)
    for i, name in enumerate(files):
        extension = magic.from_file(directory + '/' + name).partition(" ")[0].lower()
        os.rename(directory + '/' + name, directory + '/' + name + "." + extension)
    os.rename(directory, directory + ".done")
    return nb_files


# def resize_all(path, width, height):
#     files = os.listdir(path)
#     for file in files:
#         with open(file, 'r+b') as f:
#             with Image.open(f) as image:
#                 cover = resizeimage.resize_cover(image, [width, height])
#                 cover.save(file, image.format, validate=False)
#     os.rename(path, "r_" + path)


def check_step_done(step, file_name):
    if step == "url_img" and os.path.exists(file_name) is True:
        with open(file_name, "r") as text_file:
            if text_file.readlines()[-1].__contains__("Step Done."):
                return True
    if step == "download_img" and os.path.exists(file_name + ".done"):
        return True
    # if step == "resize_img" and os.path.exists("r_" + file_name + ".done"):
    #     return True
    return False


def write_in_file(file_name, dict_data):
    with open(file_name, 'a+') as text_file:
        for data in dict_data:
            print("{}".format(data), file=text_file)
        print("Step Done.", file=text_file)


def my_mkdir(path):
    try:
        os.makedirs(path)
        print("Le répertoire ", path, " à été créer.")
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def imgur(driver, category):
    list_url = []
    url = 'https://imgur.com/search?q=' + category
    driver.get(url)
    scroll_until_end(driver)
    images = driver.find_elements_by_css_selector('.image-list-link img')
    print("imgur : ", len(images), "éléments ... ", end='')
    for image in images:
        src = image.get_attribute('src')
        src = src[:27] + src[28:]  # enleve le b du string pour avoir le lien des images de bonnes qualité
        list_url.append(src)
    print("OK")
    return list(set(list_url))


def ggsearch(driver, category, quality='bad'):
    list_url = []
    url = 'https://www.google.com/search?q=' + category.replace(' ', '+')
    driver.get(url)
    driver.find_element_by_xpath('//*[@id="hdtb-msb-vis"]/div[2]/a').click()  # xpath du lien "image" de google
    scroll_until_end(driver)

    # ----------------------------
    # Bad quality Operation : Récupération de toutes les images miniature
    # ----------------------------
    if quality == 'bad':
        img_s = driver.find_elements_by_css_selector('.rg_ic.rg_i')
        bar = init_progressbar("ggsearch : " + str(len(img_s) * 7) + " éléments ... ", len(img_s)-1)
        bar.start()
        for i, img in enumerate(img_s):
            try:
                img.click()
                card_imgs_s = driver.find_elements_by_css_selector('.irc_rii')
                for card_img in card_imgs_s:
                    try:
                        src = card_img.get_attribute('src')
                        list_url.append(src)
                    except:
                        pass
                try:
                    src = img.get_attribute('src')
                    list_url.append(src)
                except:
                    pass
            except:
                pass
            bar.update(i)
        bar.finish()
    # ----------------------------
    # Fin Operation
    # ----------------------------

    # ----------------------------
    # Good quality Operation : Récupération de toutes les images en qualité original, opération longue
    # ----------------------------
    if quality == 'good':
        img_s = driver.find_elements_by_css_selector('.rg_ic.rg_i')
        print("ggsearch : ", len(img_s) * 7, "éléments ... ", end='')
        for img in img_s:
            dothis = True
            try:
                img.click()
            except:
                dothis = False

            card_imgs_s = driver.find_elements_by_css_selector('.irc_rii')
            for index, card_img in enumerate(card_imgs_s):
                if index == 7:  # card_imgs_s contient 8 éléments, le dernier étant le "aficher plus de résultat" sur
                    break  # google image, il ne faut donc pas l'inclure
                dothis2 = True
                try:
                    card_img.click()
                except:
                    dothis2 = False

                if dothis2 is True:
                    card_imgs_selected = driver.find_elements_by_css_selector('.irc_mi')
                    for card_img_selected in card_imgs_selected:
                        try:
                            src = card_img_selected.get_attribute('src')
                            list_url.append(src)
                        except:
                            pass

            # Cette partie enregistre l'image principale cliqué
            if dothis is True:
                selected_imgs = driver.find_elements_by_css_selector('.irc_mi')
                for selected_img in selected_imgs:
                    try:
                        src = selected_img.get_attribute('src')
                        list_url.append(src)
                    except:
                        pass
    return list(set(list_url))


def pexel(driver, category, quality='bad'):
    list_url = []
    url = 'https://www.pexels.com/search/' + category
    driver.get(url)
    scroll_until_end(driver)
    images = driver.find_elements_by_css_selector('.photo-item__img')
    if len(images) > LIMIT:
        print("pexel : ", LIMIT, '/', len(images), "éléments ... ", end='')
    else:
        print("pexel : ", LIMIT, '/', len(images), "éléments ... ", end='')
    if quality == 'good':
        for index, image in enumerate(images):
            src = image.get_attribute('data-big-src')
            list_url.append(src)
            if index > LIMIT:
                break
    if quality == 'bad':
        for index, image in enumerate(images):
            src = image.get_attribute('src')
            list_url.append(src)
            if index > LIMIT:
                break
    print("OK")
    return list(set(list_url))


def _init_driver(str_driver):
    try:
        if str_driver == 'PhantomJS':
            driver = webdriver.PhantomJS()
        elif str_driver == 'Chrome':
            # driver = webdriver.Chrome()  # For chrome not headless
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('headless')
            driver = webdriver.Chrome(options=chrome_options)
        else:
            print('Driver not yet supported.')
            raise Exception
    except Exception as e:
        raise e
    return driver


def count_files(path):
    files = os.listdir(path)
    return len(files)


def begin_scrap(path_dest, category, quality='bad', str_driver='Chrome'):
    my_mkdir(path_dest)
    directory_name = path_dest + category.replace(' ', '_') + "_" + quality
    file_name = category.replace(' ', '_') + "_" + quality + ".txt"
    if not check_step_done("url_img", file_name):
        print("\nCréation de ", file_name, " ... ")
        driver = _init_driver(str_driver)
        urls = ggsearch(driver, category, quality)  # + imgur(driver, category) + pexel(driver, category, quality)
        driver.close()
        write_in_file(file_name, urls)
    else:
        print(file_name, " ... OK")
    if not check_step_done("download_img", directory_name):
        nb_dl = download_all(directory_name, file_name)
    else:
        nb_dl = count_files(directory_name + ".done")
    # if not check_step_done("resize_img", directory_name):
    #     resize_all(directory_name, 64, 64)
    return nb_dl
