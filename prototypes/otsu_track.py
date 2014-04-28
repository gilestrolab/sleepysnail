__author__ = 'quentin'


import numpy as np
import cv2
import cv

cap = cv2.VideoCapture('camshift_sample2.avi')


ret,frame = cap.read()
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


while True:
    ret, orig = cap.read()
    if ret:
        frame = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
        blur_frame = cv2.blur(frame , (111,111))
        blur_frame = np.pad(blur_frame , 25, "edge")
        blur_frame[25:-25,25:-25] = frame
        morph = cv2.dilate(blur_frame, np.ones((3,3), dtype=np.uint8), iterations=5)
        morph = cv2.erode(morph, np.ones((3,3), dtype=np.uint8), iterations=8)
        morph = cv2.dilate(morph, np.ones((3,3), dtype=np.uint8), iterations=3)
        blur = cv2.medianBlur(morph, 25)


        bin = cv2.adaptiveThreshold(blur, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, 2)

        bin = bin[25:-25,25:-25]
        contours, hiera = cv2.findContours(bin, cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)

        if len(contours) == 1:
            cv2.drawContours(orig,contours, -1, (0,255,255),2)


        cv2.imshow('img', orig)

        k = cv2.waitKey(10) & 0xff
        if k == 27:
            break

    else:
        break

cv2.destroyAllWindows()
cap.release()