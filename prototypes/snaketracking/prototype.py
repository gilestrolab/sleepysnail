__author__ = 'quentin'

import cv2
import cv
from sleepysnail.acquisition.video_capture import VideoDirCapture
from acwe import MorphACWE
import numpy as np
from sleepysnail.utils.figure_maker import FigureMaker
R = 1.4
FILE = "./test.avi"





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



class Tracker(object):
    def __init__(self, r):
        self.mask = None
        l1 = 1e9
        l2 = l1 * r
        self.snake = MorphACWE(1, l1, l2)
        self.counter=0

    def make_seed(self, image, padding=25):
        blur_frame = cv2.blur(image, (151,151))
        blur_frame = np.pad(blur_frame, padding, "edge")
        blur_frame[padding:-padding, padding :-padding ] = image
        med = cv2.medianBlur(blur_frame, 15)
        morph = cv2.dilate(med, np.ones((3, 3), dtype=np.uint8), iterations=7)
        morph = cv2.erode(morph, np.ones((3, 3), dtype=np.uint8), iterations=7)
        seed = cv2.adaptiveThreshold(morph, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, 10)
        seed = seed[padding:-padding, padding :-padding]

        blobs = BlobCollection(seed, filter_fun=filter_blobs)
        if len(blobs) == 0:
            return
        elif len(blobs) >1 :
            good_blob_id = np.argmax([bl.area for bl in blobs])
            good_blob = blobs[good_blob_id]
        else:
            good_blob = blobs[0]

        self.mask= np.zeros(seed.shape, np.uint8)
        cv2.drawContours(self.mask, [good_blob.points], 0, 255, -1)



    def __call__(self, image):

        image = image[6:-6, 6:-6]
        # gaus = cv2.GaussianBlur(image, (51,51), 4.5)
        gaus_small = cv2.GaussianBlur(image, (7,7), 1.5)


        sob_x = cv2.Sobel(gaus_small, cv.CV_16S, 1,0)
        sob_x = np.abs(sob_x).astype(np.uint8)
        sob_y = cv2.Sobel(image, cv.CV_16S, 0,1)
        sob_y = np.abs(sob_y).astype(np.uint8)
        sobel = (sob_x + sob_y)/2


        test = cv2.subtract(image, sobel)

        self.make_seed(image)
        if self.mask is None:
            return

        self.snake.set_levelset(self.mask)

        epsilon = 1e-5

        es = []
        for i in range(100):
            toshow = cv2.cvtColor(image, cv.CV_GRAY2BGR)

            if i ==0:
                fig_make(toshow,"%03d_%02d" % (self.counter, i))

            old_mask = self.snake.levelset
            bc = BlobCollection(old_mask.astype(np.uint8))
            cv2.drawContours(toshow, [bc[0].points], 0, (255,200,0), 2, cv.CV_AA)

            fig_make(toshow,"%03d_%02d" % (self.counter, i+1))
            cv2.imshow("toshow",toshow)



            cv2.waitKey(10)
            self.mask = self.snake.step(test)

            # e = np.sum(np.logical_and(old_mask, self.mask))/ np.float(np.sum(np.logical_or(old_mask, self.mask)))
            e = np.sum(old_mask) / np.float(np.sum(self.mask))

            es.append(e)

            if len(es) > 5:
                if abs(es[-1] - es[-3] + es[-2] - es[-4]) < epsilon:
                    #print (i, i)
                    break
        self.counter += 1




fig_make = FigureMaker("/tmp/fig/", "snake")


if __name__ == "__main__":
    vc = VideoDirCapture(FILE)
    tr = Tracker(R)
    for i, img in enumerate(vc.read_all()):
        tr(img)

