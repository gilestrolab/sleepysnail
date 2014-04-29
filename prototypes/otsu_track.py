__author__ = 'quentin'


import numpy as np
import cv2
import cv










def filter_good_contours(contour, min_length=50, max_length=200, min_ar=1, max_ar=3):
        rect = cv2.minAreaRect(contour)
        box = cv.BoxPoints(rect)
        a = np.complex(box[0][0], box[0][1])
        b = np.complex(box[1][0], box[1][1])
        c = np.complex(box[2][0], box[2][1])
        diag = np.abs(a-c)
        aspect_ratio = np.abs(a-b)/ np.abs(c-b)
        if aspect_ratio < 1:
            aspect_ratio = 1/aspect_ratio


        if diag  > max_length or diag < min_length:
            return False

        if aspect_ratio > max_ar or aspect_ratio < min_ar:
            return False

        return True












#cap = cv2.VideoCapture('/data/sleepysnail/task-output/MakeVideoForRoi/MakeVideoForRoi-data_sleepysnail_raw_20140425-175349_0-1-5-5.027f0152af3e0f09230ea3a694a8ad0a.avi')
cap = cv2.VideoCapture('/data/sleepysnail/task-output/MakeVideoForRoi/MakeVideoForRoi-data_sleepysnail_raw_20140425-175349_0-1-5-8.027f0152af3e0f09230ea3a694a8ad0a.avi')


ret,frame = cap.read()
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

from sleepysnail.acquisition.video_capture import  VIDEO_FORMAT

vw = None



padding = 25
i = 0
while True:
    ret, orig = cap.read()
    i +=1
    if i % 1000 == 0:
        print i
    if ret:
        frame = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
        if vw is None:
            vw = cv2.VideoWriter("/tmp/sleepysnail_contours.avi", VIDEO_FORMAT["fourcc"], 25, (frame.shape[1],frame.shape[0]))

        frame = cv2.GaussianBlur(frame , (9,9), 1.5)


        blur_frame = cv2.blur(frame , (151,151))
        blur_frame = np.pad(blur_frame , padding, "edge")

        blur_frame[padding :-padding ,padding :-padding ] = frame

        med = cv2.medianBlur(blur_frame, 15)
        morph = cv2.dilate(med, np.ones((3,3), dtype=np.uint8), iterations=4)
        morph = cv2.erode(morph, np.ones((3,3), dtype=np.uint8), iterations=4)

        binary = cv2.adaptiveThreshold(morph, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, 7)
        binary = cv2.dilate(binary, np.ones((3,3), dtype=np.uint8), iterations=7)

        orig_bin = cv2.adaptiveThreshold(blur_frame, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, -5)
        orig_bin = cv2.dilate(orig_bin, np.ones((3,3), dtype=np.uint8), iterations=2)

        binary = cv2.bitwise_and(orig_bin, binary)


        binary = binary[padding :-padding ,padding :-padding ]
        contours, hiera = cv2.findContours(binary, cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)

        contours = contours = filter(filter_good_contours, contours)

        contours = [cv2.approxPolyDP(c, 1, True) for c in contours]

        cv2.drawContours(orig, contours, -1, (0,255,255), 2, cv.CV_AA)


        #cv2.imshow('img', orig)

        vw.write(orig)
        #k = cv2.waitKey(10) & 0xff
        #if k == 27:
        #    break

    else:
        break

cv2.destroyAllWindows()
cap.release()