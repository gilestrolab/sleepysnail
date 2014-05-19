from ubuntuone.controlpanel.gui.qt import gotoweb

__author__ = 'quentin'

import cv
import cv2
import numpy as np

def filter_blobs( blobs, min_length=30, max_length=200, min_ar=1, max_ar=3):
    out = []
    for b in blobs:
        if not b.is_valid:
            continue

        if b.w > max_length or b.h < min_length:
            continue

        if b.aspect_ratio > max_ar or b.aspect_ratio < min_ar:
            continue
        out.append(b)
    return out

class Blob(object):
    def __init__(self, array, epsilon=-1, resample=-1):

        try:

            self.points = np.copy(array)

            if epsilon > 0:
                self.points = cv2.approxPolyDP(self.points, epsilon, True)
            if resample > 0:
                pass

            self.moments = cv2.moments(self.points, False)
            zeroth = self.moments["m00"]
            self.x = self.moments["m10"] / zeroth
            self.y = self.moments["m01"] / zeroth
            self.area = cv2.contourArea(self.points)
            self.perim = cv2.arcLength(self.points,True)
            self.hull = cv2.convexHull(self.points)

            self.area_hull = cv2.contourArea(self.hull)
            self.perim_hull = cv2.arcLength(self.hull,True)


            rect = cv2.minAreaRect(self.points)
            box = cv.BoxPoints(rect)
            a = np.complex(box[0][0], box[0][1])
            b = np.complex(box[1][0], box[1][1])
            c = np.complex(box[2][0], box[2][1])

            self.w, self.h = sorted([np.abs(a-b), np.abs(c-b)])
            self.is_valid = True
        except ZeroDivisionError:
            self.is_valid = False

    @property
    def aspect_ratio(self):
        return self.h / self.w

class BlobCollection(object):

    def __init__(self, image, epsilon=-1, resample=-1, filter_fun=None, *filter_args, **filter_kwargs):

        self.blob_list = []
        contours, hiera = cv2.findContours(image, cv.CV_RETR_EXTERNAL, cv.CV_CHAIN_APPROX_SIMPLE)
        for c in contours:
            bl = Blob(c, epsilon, resample)

            if not (bl is None):
                self.blob_list.append(bl)



        if not filter_fun is None:
            self.blob_list = filter_fun(self.blob_list, *filter_args, **filter_kwargs)


    def __iter__(self):

        for bl in self.blob_list:
            yield bl
    def __len__(self):
        return len(self.blob_list)
    def __getitem__(self,k):
        return self.blob_list[k]

class BlobFinder(object):
    def __init__(self, padding):
        self.padding = padding
        self.background_classif = cv2.NormalBayesClassifier()

        pass

    def header(self):
        return "x, y, area, perim, hull_area, hull_perim, w, h"

    @property
    def n_features(self):
         stri= self.header()
         return len(stri.split(","))

    def __na_result(self):
        return ",".join(["NA" for i in range(self.n_features)])

    def __filter_good_contours(self, contour, min_length=30, max_length=200, min_ar=1, max_ar=3):
        rect = cv2.minAreaRect(contour)
        box = cv.BoxPoints(rect)
        a = np.complex(box[0][0], box[0][1])
        b = np.complex(box[1][0], box[1][1])
        c = np.complex(box[2][0], box[2][1])

        w, h = sorted([np.abs(a-b), np.abs(c-b)])

        if w > max_length or h < min_length:
            return False

        aspect_ratio = w/h

        if aspect_ratio > max_ar or aspect_ratio < min_ar:
            return False

        return True



    def __make_seed(self, image):
        padding = self.padding


        blur_frame = cv2.blur(image, (151,151))
        blur_frame = np.pad(blur_frame, padding, "edge")

        blur_frame[padding:-padding, padding :-padding ] = image

        med = cv2.medianBlur(blur_frame, 15)
        morph = cv2.dilate(med, np.ones((3, 3), dtype=np.uint8), iterations=7)
        morph = cv2.erode(morph, np.ones((3, 3), dtype=np.uint8), iterations=7)

        seed = cv2.adaptiveThreshold(morph, 1,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, 7)
        seed = seed[padding:-padding, padding :-padding]




        blobs = BlobCollection(seed, filter_fun=filter_blobs)
        if len(blobs) != 1:
            return

        seed = np.zeros(seed.shape, np.uint8)
        cv2.drawContours(seed, [bl.points for bl in blobs], 0, 1, -1)

        return seed, bl.x, bl.y


    def find_blobs(self, image):


        image = image[6:-6, 6:-6]
        frame = cv2.GaussianBlur(image, (9,9), 1.5)

        seed_tuple = self.__make_seed(frame)
        if seed_tuple is None:
            return image, self.__na_result()
        seed, seed_x, seed_y = seed_tuple

        # pixels that could be part of the blob:
        relaxed_bin = cv2.adaptiveThreshold(frame, 1,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, -5)
        relaxed_bin = cv2.dilate(relaxed_bin, np.ones((3, 3), dtype=np.uint8), iterations=5)

        seed_center = complex(seed_x, seed_y)

        x_mat = np.fromfunction(lambda i, j: j, seed.shape)
        y_mat = np.fromfunction(lambda i, j: i, seed.shape)

        y_vec = y_mat.flatten() * 1j
        x_vec = x_mat.flatten()
        pixel_posit = y_vec + x_vec

        dist_mat = np.abs(pixel_posit - seed_center).astype(np.float32)

        grey_mat = image.flatten().astype(np.float32)
        data = np.column_stack((dist_mat , grey_mat))

        labels = (relaxed_bin + seed).flatten()



        if len(np.unique(labels)) < 3:
            print "labels issue"
            return image, self.__na_result()

        train_data = data[labels != 1, :]
        test_data = data[labels == 1, :]
        response = labels[labels != 1]

        self.background_classif.train(train_data, response.astype(np.int32))
        _, predicted = self.background_classif.predict(test_data)

        labels[labels == 1] = predicted

        prediction = labels.reshape(seed.shape)
        prediction = cv2.erode(prediction, np.ones((3, 3), dtype=np.uint8), iterations=1)
        prediction = cv2.dilate(prediction, np.ones((3, 3), dtype=np.uint8), iterations=1)

        blobs = BlobCollection(prediction, epsilon=1, filter_fun=filter_blobs)


        if len(blobs) != 1:
            return image, self.__na_result()
        bl = blobs[0]


        features = (bl.x, bl.y, bl.area, bl.perim, bl.area_hull, bl.perim_hull, bl.w, bl.h)
        assert len(features) == self.n_features

        out = ",".join(str(i) for i in features)

        # log image
        cv2.drawContours(image, [bl.points], 0, (255,0,0), 4)


        return image, out

