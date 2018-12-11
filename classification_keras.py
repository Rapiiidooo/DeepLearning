import gc
import os
import cv2
import magic
import numpy as np
import keras
from keras.engine.saving import model_from_json
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical, np_utils
from keras.models import Sequential
from keras.layers import Conv2D, MaxPool2D, Flatten, Dense, MaxPooling2D, Dropout
from keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
from keras.optimizers import SGD
from scraping_selenium import my_mkdir
from matplotlib import pyplot

SCORE_FILE = "_score.txt"


def generate_more_data(path_src, nb_multiplied):
    datagen = ImageDataGenerator(
        rotation_range=40,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest')

    total_files = 0
    directories = os.listdir(path_src)
    for directory in directories:
        files = os.listdir(path_src + directory)
        total_files += len(files)
        for i, file in enumerate(files):
            try:
                format_img = magic.from_file(path_src + directory + "/" + file).partition(" ")[0].lower()
                img = load_img(path_src + directory + "/" + file)  # this is a PIL image
                x = img_to_array(img)  # this is a Numpy array with shape (3, 150, 150)
                x = x.reshape((1,) + x.shape)  # this is a Numpy array with shape (1, 3, 150, 150)

                # the .flow() command below generates batches of randomly transformed images
                # and saves the results to the path_src directory
                j = 0
                for batch in datagen.flow(x,
                                          batch_size=1,
                                          save_to_dir=path_src + directory,
                                          save_prefix=file[:-4],
                                          save_format=format_img):
                    j += 1
                    if j >= nb_multiplied:
                        break
            except Exception as e:
                print(e)
                pass
        files = os.listdir(path_src + directory)
        total_files += len(files)
    return total_files


def iter_images(width, height, path_src, path_dataset):
    img_data = []
    img_data_set = []
    labels = []
    labels_set = []
    print("Trying to iter over the images " + str(width) + 'x' + str(height) + " (make datalist resized) ...")
    directories = os.listdir(path_src)
    for i, directory in enumerate(directories):
        files = os.listdir(path_src + directory)
        print(len(files), '... ', end='')
        for file in files:
            try:
                img = cv2.imread(path_src + directory + "/" + file)
                img = cv2.resize(img, (width, height))
                img_data.append(img)
                labels.append(i)
            except:
                pass
        print('OK')
    if path_dataset is not None:
        img_data_set, labels_set = iter_images(width, height, path_dataset, None)
    return img_data + img_data_set, labels + labels_set


def load_model(path_src):
    json_file = open(path_src + ".json", 'r')
    model_json = json_file.read()
    model = model_from_json(model_json)
    model.load_weights(path_src + ".h5")
    model._make_predict_function()
    model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])
    return model


def get_nb_model():
    return [0, 1, 2]


def train_model(x_train, y_train, nb_classes, batch_size, epochs, num_model):
    model = Sequential()
    if num_model == 0:
        model.add(Conv2D(32, (3, 3), input_shape=(batch_size, batch_size, 3), activation='relu'))
        model.add(MaxPool2D(pool_size=(2, 2)))
        model.add(Flatten())
        model.add(Dense(batch_size, activation='relu'))
        model.add(Dense(nb_classes, activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])
    elif num_model == 1:
        model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(batch_size, batch_size, 3)))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        model.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
        model.add(Conv2D(batch_size, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        model.add(Flatten())
        model.add(Dense(batch_size, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(nb_classes, activation='softmax'))
        model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    elif num_model == 2:
        # VGG-like convnet from documentation
        model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(batch_size, batch_size, 3)))
        model.add(Conv2D(32, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(Conv2D(64, (3, 3), activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))
        model.add(Flatten())
        model.add(Dense(256, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(nb_classes, activation='softmax'))
        sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
        model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])
    else:
        print('Model number : ' + num_model + ' is not supported')
        return

    history = model.fit(x_train, y_train,
                        batch_size=batch_size,
                        epochs=epochs,
                        verbose=1,
                        validation_split=0.2)
    return model, history


def plot_history(history, dest_model):
    loss_list = [s for s in history.history.keys() if 'loss' in s and 'val' not in s]
    val_loss_list = [s for s in history.history.keys() if 'loss' in s and 'val' in s]
    acc_list = [s for s in history.history.keys() if 'acc' in s and 'val' not in s]
    val_acc_list = [s for s in history.history.keys() if 'acc' in s and 'val' in s]

    if len(loss_list) == 0:
        print('Loss is missing in history')
        return

    epochs = range(1, len(history.history[loss_list[0]]) + 1)

    pyplot.figure(1)
    for l in loss_list:
        pyplot.plot(epochs, history.history[l], 'b',
                    label='Training loss (' + str(str(format(history.history[l][-1], '.5f')) + ')'))
    for l in val_loss_list:
        pyplot.plot(epochs, history.history[l], 'g',
                    label='Validation loss (' + str(str(format(history.history[l][-1], '.5f')) + ')'))
    pyplot.title('Loss')
    pyplot.xlabel('Epochs')
    pyplot.ylabel('Loss')
    pyplot.legend()

    ## Accuracy
    pyplot.figure(2)
    for l in acc_list:
        pyplot.plot(epochs, history.history[l], 'b',
                    label='Training accuracy (' + str(format(history.history[l][-1], '.5f')) + ')')
    for l in val_acc_list:
        pyplot.plot(epochs, history.history[l], 'g',
                    label='Validation accuracy (' + str(format(history.history[l][-1], '.5f')) + ')')
    pyplot.title('Accuracy')
    pyplot.xlabel('Epochs')
    pyplot.ylabel('Accuracy')
    pyplot.legend()
    pyplot.savefig(dest_model)
    pyplot.clf()


def save_model(model, history, path_dest):
    my_mkdir('model')
    model_dest = 'model/' + path_dest
    model.save(model_dest + '.h5')
    model_json = model.to_json()
    with open(model_dest + ".json", "w") as json_file:
        json_file.write(model_json)

    # Save to png the histories
    try:
        plot_history(history, model_dest + '.png')
    except:
        pass


def save_scores(dest_model, model, x_test, y_test):
    score = model.evaluate(x_test, y_test, verbose=0)
    with open(SCORE_FILE, "a+") as scores_file:
        print("{} : {}"
              .format(dest_model, "%.2f%%" % (score[1] * 100)),
              file=scores_file)


def gen_model(dest_model, batch_size, epochs, nb_classes, num_model, path_data, path_dataset=None):
    img_data, labels = iter_images(batch_size, batch_size, path_data, path_dataset)

    data = np.asarray(img_data)
    data = data.astype('float32') / 255.0

    labels = np.asarray(labels)

    # Split the data
    x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0.30, shuffle=True)

    np_utils.normalize(x_train)
    np_utils.normalize(x_test)

    y_train_binary = to_categorical(y_train, num_classes=nb_classes)
    y_test_binary = to_categorical(y_test, num_classes=nb_classes)

    if os.path.exists(dest_model):
        model = load_model(dest_model)
    else:
        model, history = train_model(x_train, y_train_binary, nb_classes, batch_size, epochs, num_model)
        save_model(model, history, dest_model)
        del history
    save_scores(dest_model, model, x_test, y_test_binary)
    del model
    keras.backend.clear_session()
    gc.collect()


def classify_data_from_model(model, path_data, batch_size):
    img_data = []
    files = os.listdir(path_data)
    for file in files:
        try:
            img = cv2.imread(path_data + "/" + file)
            img = cv2.resize(img, (batch_size, batch_size))
            img_data.append(img)
        except:
            pass

    data = np.asarray(img_data)
    data = data.astype('float32') / 255.0
    pred = model.predict(data, batch_size, verbose=0)
    for i in range(len(pred)):
        print(pred[i])
