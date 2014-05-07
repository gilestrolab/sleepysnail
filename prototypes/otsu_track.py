__author__ = 'quentin'


import numpy as np
import cv2
import cv
import scipy.stats



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
cap = cv2.VideoCapture('/data/sleepysnail/task-output/MakeVideoForRoi/MakeVideoForRoi-data_sleepysnail_raw_20140425-175349_0-1-5-4.91f12cdcf463b198be758002863d0372.avi')




from sleepysnail.acquisition.video_capture import  VIDEO_FORMAT

vw = None

padding =25
background_classif = cv2.NormalBayesClassifier()
criteria=cv2.TERM_CRITERIA_MAX_ITER | cv2.TERM_CRITERIA_EPS
parameters = dict(max_depth=7, min_sample_count=5, use_surrogates=False, nactive_vars=0,
                      term_crit=(criteria, 50, 1))

# background_classif = cv2.RTrees()
#
# background_classif = cv2.ANN_MLP(np.array([4,5, 5,3, 1]),  cv2.ANN_MLP_SIGMOID_SYM)
#

i = 0
while True:
    cv2.waitKey(10)
    ret,frame = cap.read()
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    image = image[4:-4, 4:-4]
    frame = cv2.GaussianBlur(image , (9,9), 1.5)

    blur_frame = cv2.blur(frame, (151,151))
    blur_frame = np.pad(blur_frame, padding, "edge")

    blur_frame[padding:-padding, padding :-padding ] = frame

    med = cv2.medianBlur(blur_frame, 15)
    morph = cv2.dilate(med, np.ones((3, 3), dtype=np.uint8), iterations=7)
    morph = cv2.erode(morph, np.ones((3, 3), dtype=np.uint8), iterations=7)

    seed = cv2.adaptiveThreshold(morph, 1,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, 7)
    seed = seed[padding:-padding, padding :-padding]

    seed_contours, hiera =cv2.findContours(seed, cv.CV_RETR_EXTERNAL,cv.CV_CHAIN_APPROX_SIMPLE)
    cv2.drawContours(seed,seed_contours, 0, 1, -1)

    relaxed_bin = cv2.adaptiveThreshold(frame, 1,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, -5)
    relaxed_bin  = cv2.dilate(relaxed_bin , np.ones((3, 3), dtype=np.uint8), iterations=5)
    if len(seed_contours) != 1:
        continue

    mom= cv2.moments(seed_contours[0], False)
    zeroth = mom["m00"]
    x = mom["m10"] / zeroth
    y = mom["m01"] / zeroth

    seed_center = complex(x, y)

    x_mat = np.fromfunction(lambda i, j: j, seed.shape)
    y_mat = np.fromfunction(lambda i, j: i, seed.shape)

    y_vec = y_mat.flatten() * 1j
    x_vec = y_mat.flatten()


    pixel_posit = y_vec + x_vec
    dist_mat = np.abs(pixel_posit - seed_center).astype(np.float32)
    grey_mat = image.flatten().astype(np.float32)
    med_mat = cv2.medianBlur(image, 31).flatten().astype(np.float32)

    data = np.column_stack((dist_mat , grey_mat))

    print data.shape

    labels = (relaxed_bin + seed).flatten()
    cv2.imshow("q", 100* (relaxed_bin + seed))
    if len(np.unique(labels)) < 3:
        continue



    train_data = data[labels != 1, :]
    test_data = data[labels == 1, :]
    response = labels[labels != 1]

    weights = 1.0 + (response).astype(np.float32) / 2.0



    background_classif.train(train_data, response.astype(np.int32))
    _, predicted = background_classif.predict(test_data)




    # background_classif.train(train_data, cv2.CV_ROW_SAMPLE,  response.astype(np.float32), params=parameters)
    # predicted = np.array([background_classif.predict(td) for td in test_data], dtype=np.float32)

    # background_classif.train(train_data,  response.astype(np.float32), weights)
    # _, predicted = background_classif.predict(test_data)
    # #
    # #
    # #
    # labels = labels.astype(np.float32)
    # #
    labels[labels == 1] = predicted
    #
    # good_labs = labels > 1.8
    # labels[good_labs] = 1
    # labels[np.bitwise_not(good_labs)] = 0

    prediction = labels.reshape(seed.shape)
    prediction = cv2.erode(prediction , np.ones((3, 3), dtype=np.uint8), iterations=1)
    prediction = cv2.dilate(prediction , np.ones((3, 3), dtype=np.uint8), iterations=1)


    cv2.imshow("test", cv2.merge([image, prediction*100, 255-image]))




    #cv2.imshow("test", (dist_mat.reshape(seed.shape)/np.max(dist_mat))**3)
    #cv2.imshow("test", 100*(test+ seed))

    #test + seed


    continue

#    orig_bin = cv2.adaptiveThreshold(image, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, -5)

    #orig_bin = cv2.dilate(orig_bin, np.ones((3,3), dtype=np.uint8), iterations=2)
    #cv2.imshow("oribin", orig_bin + seed /2)

    binary = cv2.bitwise_and(orig_bin, binary)
    binary = binary[padding :-padding ,padding :-padding ]

    contours, hiera = cv2.findContours(binary, cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)

    contours = filter(filter_good_contours, contours)
    contours = [cv2.approxPolyDP(c, 1, True) for c in contours]

    if len(contours) == 1:

        mom= cv2.moments(contours[0], False)

        zeroth = mom["m00"]
        x = mom["m10"] / zeroth
        y = mom["m01"] / zeroth
        area = zeroth
        # features = (id, f, x, y, area)
        # out = ",".join(str(i) for i in features)


