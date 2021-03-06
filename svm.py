# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import tensorflow as tf


class SVM:
    label_feature_list = []
    column_dict = {}
    class_list = []

    def set_edited_data_frame(self, csv_path):
        self.edited_data_frame = pd.read_csv(csv_path, index_col=0)

    def set_not_edited_data_frame(self, csv_path):
        self.not_edited_data_frame = pd.read_csv(csv_path, index_col=0)

    def set_list_dict(self, list_dict):
        self.list_dict = list_dict

    def set_steps(self, steps):
        self.steps = steps

    def __init__(self, edited_csv_path, not_edited_csv_path, list_dict, model_dir='./output', steps=100):
        self.edited_data_frame = None
        self.not_edited_data_frame = None
        self.list_dict = None
        self.metrics = {}
        self.results = {}
        self.set_edited_data_frame(edited_csv_path)
        self.set_not_edited_data_frame(not_edited_csv_path)
        self.model_dir = model_dir
        self.set_steps(steps)

        if self.edited_data_frame.shape[0] != self.not_edited_data_frame.shape[0]:
            raise ValueError('The number of features must be equal in edited e not edited images')

        self.set_list_dict(list_dict)

        for line in range(1, self.edited_data_frame.shape[0] + 1):
            SVM.label_feature_list.append(tf.contrib.layers.real_valued_column('f%d' % line))

        self.svm = tf.contrib.learn.SVM(feature_columns=SVM.label_feature_list, example_id_column='example_id',
                                        model_dir=self.model_dir)

    @staticmethod
    def input_fn():
        _column_dict = {'example_id': tf.constant(SVM.column_dict['example_id'])}
        for line in range(len(SVM.label_feature_list)):
            _column_dict[SVM.label_feature_list[line][0]] = tf.constant(
                SVM.column_dict[SVM.label_feature_list[line][0]])
        return _column_dict, tf.constant(SVM.class_list)

    @staticmethod
    def predict_fn():
        _column_dict = {}
        for line in range(len(SVM.label_feature_list)):
            _column_dict[SVM.label_feature_list[line][0]] = tf.constant(
                SVM.column_dict[SVM.label_feature_list[line][0]])
        return _column_dict

    def fill_features(self, edited_image_names, not_edited_image_names):
        col = 0
        for image in edited_image_names:
            values = self.edited_data_frame[image].values.astype(np.float32)
            for line in range(self.edited_data_frame.shape[0]):
                self.column_dict[SVM.label_feature_list[line][0]][col] = values[line]
            col += 1

        for image in not_edited_image_names:
            values = self.not_edited_data_frame[image].values.astype(np.float32)
            for line in range(self.not_edited_data_frame.shape[0]):
                self.column_dict[SVM.label_feature_list[line][0]][col] = values[line]
            col += 1

    def create_dictionary(self, edited_images, not_edited_images):
        images = edited_images + not_edited_images
        num_images = len(images)
        self.class_list = np.zeros(num_images, np.uint8)
        self.class_list[:len(edited_images)] = 1

        for feature in SVM.label_feature_list:
            self.column_dict[feature[0]] = np.zeros(num_images, np.float32)

        self.fill_features(edited_images, not_edited_images)

    def fit(self):
        self.column_dict = {
            'example_id': self.list_dict['seam carved']['training'] + self.list_dict['untouched']['training']}
        self.create_dictionary(self.list_dict['seam carved']['training'], self.list_dict['untouched']['training'])

        SVM.column_dict = self.column_dict
        SVM.class_list = self.class_list
        self.svm.fit(input_fn=SVM.input_fn, steps=self.steps)

    def evaluate(self):
        self.column_dict = {
            'example_id': self.list_dict['seam carved']['validation'] + self.list_dict['untouched']['validation']}
        self.create_dictionary(self.list_dict['seam carved']['validation'], self.list_dict['untouched']['validation'])

        SVM.column_dict = self.column_dict
        SVM.class_list = self.class_list
        self.metrics = self.svm.evaluate(input_fn=SVM.input_fn, steps=self.steps)
        return self.metrics['accuracy']

    def predict(self):
        del self.column_dict['example_id']
        self.create_dictionary(self.list_dict['seam carved']['testing'], self.list_dict['untouched']['testing'])

        SVM.column_dict = self.column_dict
        self.results = self.svm.predict(input_fn=SVM.predict_fn)
        class_result = list(map(lambda x: x['classes'], self.results))
        num_edited = len(self.list_dict['seam carved']['testing'])
        hit = 0

        for index, clazz in list(enumerate(class_result)):
            if (index < num_edited and clazz == 1) or (index >= num_edited and clazz == 0):
                hit += 1

        return hit / (num_edited + len(self.list_dict['untouched']['testing'])) * 100


if __name__ == '__main__':
    from lists import ImageList

    directory = '/home/jota/Downloads/'
    dic = ImageList(directory + 'seam_images', 500, 10, 10)
    svm = SVM(directory + 'sc.csv', directory + 'nao.csv', dic.list)
    svm.fit()
    accuracy = svm.evaluate()
    print("Accuracy", accuracy)
    result = svm.predict()
    print("%f%%" % result)
