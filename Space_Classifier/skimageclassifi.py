from sklearn.linear_model import SGDClassifier
from skimage import io
import matplotlib.image as img
from astropy.io import fits
import numpy
import PIL.Image as Image

def train_model(training_features, training_targets):

    clf = SGDClassifier()

    # training features must be an array of data arrays
    # training targets must be an array of integer labels
    clf.fit(training_features,training_targets)

    return clf

from joblib import dump
def save_model(classifier, file_name):
    # save the model to the given file_name
    dump(classifier, file_name)

from joblib import load
def load_model(file_name):
    # load the model from the given file_name
    loaded_clf = load(file_name)
    return loaded_clf

import DynamoConnect
from urllib.request import urlretrieve
import os
def import_data():
    """
    Downloads all the image files in the database to the local images folder.
    """

    database_image_ids = DynamoConnect.get_image_ids()

    print("database ids:", database_image_ids)

    this_directory = os.path.dirname(__file__)

    local_images_file = open(os.path.join(this_directory, "Images", "image_ids.list"), "r+")
    local_image_ids = local_images_file.read().splitlines()

    print("local ids:", local_image_ids)

    i = 0

    for identifier in database_image_ids:

        if i > 50:
            break
        
        i += 1

        if any(identifier in id_value for id_value in local_image_ids):
            print("identifier", identifier, "found")
            continue

        # download the image from s3
        image_link = DynamoConnect.get_image_link(identifier)

        image_name = identifier + ".jpg"
        image_location = os.path.join(this_directory, "Images", image_name)

        print("Image Link:", image_link)

        urlretrieve(image_link, image_location)

        # resize image to standard size
        Image.open(image_location).resize((28,28), Image.ANTIALIAS).save(image_location)

        print(identifier,file=local_images_file)

    local_images_file.close

def load_data():
    
    this_directory = os.path.dirname(__file__)

    local_images_file = open(os.path.join(this_directory, "Images", "image_ids.list"), "r+")
    local_image_ids = local_images_file.read().splitlines()

    validation_arrays = []
    validation_labels = []
    training_arrays = []
    training_labels = []

    for identifier in local_image_ids:
        image_name = identifier + ".jpg"
        image_location = os.path.join(this_directory, "Images", image_name)
        array = io.imread(image_location, as_gray=True).flatten()

        image_info = DynamoConnect.get_image_info(identifier)

        # determine the label value
        if image_info['Label'] == 'comet':
            label = 0
        else :
            label = 1

        if image_info['Validation']:
            print("Adding to validation set:", identifier)
            validation_arrays.append(array)
            validation_labels.append(label)
        else :
            print("Adding to training set:", identifier)
            training_arrays.append(array)
            training_labels.append(label)
        
    # return two tuples, training and validation tuples
    return (training_arrays, training_labels), (validation_arrays, validation_labels)

from sklearn.model_selection import cross_val_predict
from sklearn.metrics import confusion_matrix
def main():
    # use the database images
    (training_features,training_targets), (validation_features, validation_targets) = load_data()

    clf_model = train_model(training_features,training_targets)

    test_predictions = cross_val_predict(clf_model, validation_features, validation_targets, cv=3)

    print("Test Predictions:", test_predictions)

    print("Actual:", training_targets)

    conf_matrix = confusion_matrix(validation_targets, test_predictions)

    print(conf_matrix)

if __name__ == "__main__":
    main()