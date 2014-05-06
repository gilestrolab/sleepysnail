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
cap = cv2.VideoCapture('/data/sleepysnail/task-output/MakeVideoForRoi/MakeVideoForRoi-data_sleepysnail_raw_20140425-175349_0-1-5-0.91f12cdcf463b198be758002863d0372.avi')




from sleepysnail.acquisition.video_capture import  VIDEO_FORMAT

vw = None




i = 0
while True:
    cv2.waitKey(100)
    ret,frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    padding = 25
    frame = cv2.GaussianBlur(frame , (9,9), 1.5)

    blur_frame = cv2.blur(frame, (151,151))
    blur_frame = np.pad(blur_frame, padding, "edge")

    blur_frame[padding:-padding, padding :-padding ] = frame

    med = cv2.medianBlur(blur_frame, 15)
    morph = cv2.dilate(med, np.ones((3, 3), dtype=np.uint8), iterations=4)
    morph = cv2.erode(morph, np.ones((3, 3), dtype=np.uint8), iterations=4)

    binary = cv2.adaptiveThreshold(morph, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, 7)

    cv2.imshow("binary", binary)

    #binary = cv2.dilate(binary, np.ones((3,3), dtype=np.uint8), iterations=7)

    kmask = cv2.dilate(binary, None,iterations=50)
    cv2.imshow("kmask", kmask)
    kmask_bool = kmask.flatten() > 0
    #kmask = kmask[padding :-padding ,padding :-padding ]
    hist, _ = np.histogram(blur_frame.flatten()[kmask_bool], 16, range=(0,256), normed=True)
    #hist = cv2.calcHist([blur_frame], [0], binary, [16], [0, 256])
    print hist
    back_proj = cv2.calcBackProject(blur_frame.astype('float32'), [0], hist, ranges=(0,255), scale=1)
    cv2.imshow("back_proj", blur_frame)
    print blur_frame.astype('float32').shape
    print back_proj.shape

#     ref_mean = np.mean(blur_frame[binary == 255])
#
#     grey = blur_frame.flatten().astype(np.float32)
#
#     grey = abs(grey - ref_mean)
#
#
#     x = np.fromfunction(lambda i,j: j, blur_frame.shape, dtype=np.float32).flatten(0)
#     y = np.fromfunction(lambda i,j: i, blur_frame.shape, dtype=np.float32).flatten(0)
#
#     def center_red(a):
#         return a - np.mean(a) / np.std(a)
#
#     x, y, grey = x/max(x),y/max(y), center_red(grey)
#
#     data = np.column_stack((grey*100,x, y))
#
#
#     criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
#
#     data_masked = data[kmask_bool , :]
#     if data_masked.shape[0]<2:
#         continue
#
#     labels = 1+ binary.flatten().astype(np.uint16) /255
#     print np.unique(labels)
#     _, labs_masked, centre = cv2.kmeans(data_masked, 2, criteria, 10, cv2.KMEANS_PP_CENTERS)
# #    _, labs_masked, centre = cv2.kmeans(data_masked, 2, criteria, 10, cv2.KMEANS_USE_INITIAL_LABELS, labels)
#
#     labs = np.zeros(grey.shape, np.uint8)
#
#     labs[kmask_bool] = (labs_masked )*100
#     toshow = labs.reshape(blur_frame.shape)

    #'cv2.imshow("kmeans", toshow)


    # orig_bin = cv2.adaptiveThreshold(blur_frame, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, -5)
    # orig_bin = cv2.dilate(orig_bin, np.ones((3,3), dtype=np.uint8), iterations=2)
    #
    # binary = cv2.bitwise_and(orig_bin, binary)
    # binary = binary[padding :-padding ,padding :-padding ]
    # contours, hiera = cv2.findContours(binary, cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)
    #
    # contours = filter(filter_good_contours, contours)
    # contours = [cv2.approxPolyDP(c, 1, True) for c in contours]
    #


