__author__ = 'quentin'

import cv2
import cv
import numpy as np


def filter_good_contours(c,min_length=200, max_length=500, min_ar = 3.5, max_ar = 6, max_angle=20):
            rect = cv2.minAreaRect(c)
            box = cv.BoxPoints(rect)
            a = np.complex(box[0][0], box[0][1])
            b = np.complex(box[1][0], box[1][1])
            c = np.complex(box[2][0], box[2][1])
            diag = np.abs(a-c)
            aspect_ratio = np.abs(a-b)/ np.abs(c-b)
            if aspect_ratio < 1:
                aspect_ratio = 1/aspect_ratio
            #print diag
            if diag  > max_length or diag < min_length:
                return False

            if aspect_ratio  > max_ar or aspect_ratio < min_ar:
                return False
            if abs(rect[2]% 90) > max_angle and abs(rect[2]) > max_angle:
                return False
            return True

class ROISplitter(object):
    def __init__(self, image):
        self.h_morph_line = np.array([[0,0,0], [1,1,1], [0,0,0]],dtype=np.uint8)
        self.v_morph_line = np.array([[0,1,0], [0,1,0], [0,1,0]],dtype=np.uint8)
        self.rois = self.make_rois(image)

    def make_rois(self, image, expected_number=18):
        """
        Find ROIs in the preprocessed image
        :param image: greyscale image(CV_U8C1)
        :return: a list of contours (1 per ROI)
        """

        # we try different thresholds to get all the contours
        for threshold_value in range(0, 101,5):
            preprocessed_mat = self.pre_process(image)
            _ , bin_mat = cv2.threshold(preprocessed_mat, threshold_value, 255,cv.CV_THRESH_BINARY_INV)
            contours, hiera = cv2.findContours(bin_mat, cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)

            #remove holes
            contours = [c for (c,h) in zip(contours,hiera[0]) if h[3] == -1 and len(c) >3]
            contours = filter(filter_good_contours,contours)


            if len(contours)==expected_number:
                break

        assert(len(contours)==expected_number)
        return contours

        boxes = [np.int0(cv.BoxPoints(cv2.minAreaRect(c))) for c in contours]
        rectangles = [cv2.minAreaRect(c) for c in contours]
        rot_mats = [cv2.getRotationMatrix2D(tuple((np.array(r[0]) - np.array(r[1])) * 2),
                                 r[2], 1.0)  for r in rectangles]

        sizes = []
        for box in boxes:
            a = np.complex(box[0][0], box[0][1])
            b = np.complex(box[1][0], box[1][1])
            c = np.complex(box[2][0], box[2][1])
            sizes.append((int(np.abs(c-b)), int(np.abs(a-b))))
        subimgs = [grid_img[r[0][0]:r[1][0], r[0][1]:r[1][1]] for r in rectangles]
#rotated = [cv2.warpAffine(ai, m, s) for m, s, si in zip(rot_mats, sizes,subimgs)]

        #preprocessed_mat

    def pre_process(self, image, iter_first_pass=10, iter_second_pass=64):
        """
        Preprocessed the frame of a grid and return only the vertical and horizontal, contrasted, lines

        :param image: the original image (CV_U8C1)
        :param iter_first_pass: number of erosions/dilatations in first pass
        :param iter_second_pass: number of erosions/dilatations in second  pass
        :return: an image (CV_U8C1)
        """

        # vertically close
        v_dilated_mat  = cv2.dilate(image, self.v_morph_line, iterations=iter_first_pass)
        v_eroded_mat = cv2.erode(v_dilated_mat, self.v_morph_line, iterations=iter_first_pass)

        # horizontally eroded
        h_dilated_mat  = cv2.dilate(image, self.h_morph_line, iterations=iter_first_pass)
        h_eroded_mat = cv2.erode(h_dilated_mat, self.h_morph_line, iterations=iter_first_pass)

        sqr_dilated_mat  = cv2.dilate(image, None, iterations=10)

        h_diff_img = cv2.subtract(sqr_dilated_mat, h_eroded_mat)
        h_diff_img = cv2.erode(h_diff_img, self.h_morph_line, iterations=iter_second_pass)
        h_diff_img = cv2.dilate(h_diff_img, self.h_morph_line, iterations=iter_second_pass)

        v_diff_img = cv2.subtract(sqr_dilated_mat, v_eroded_mat)
        v_diff_img = cv2.erode(v_diff_img, self.v_morph_line, iterations=iter_second_pass)
        v_diff_img = cv2.dilate(v_diff_img, self.v_morph_line, iterations=iter_second_pass)

        diff_img = cv2.add(v_diff_img, h_diff_img)
        diff_img  = cv2.dilate(diff_img,None, iterations=3)
        med_img = cv2.medianBlur(diff_img, 101)
        diff_img = cv2.subtract(diff_img, med_img)
        return diff_img

    def split_frame(self):
        pass