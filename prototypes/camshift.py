__author__ = 'quentin'



import cv2
import cv2.cv as cv
import numpy as np

class CAMShift:
    def __init__(self, source=None, bb=None):
        self.mouse_p1 = None
        self.mouse_p2 = None
        self.mouse_drag = False
        self.bb = None
        self.img = None
        if source:
            self.cam = cv2.VideoCapture(source)
        else:
            self.cam = cv2.VideoCapture(0)
        if not bb:
            self.start()
        else:
            self.bb = bb
            _, self.img = self.cam.read()
            self.lk()

    def start(self):
        _, self.img = self.cam.read()
        cv2.imshow("img", self.img)
        cv.SetMouseCallback("img", self.__mouseHandler, None)
        if not self.bb:
            _, self.img = self.cam.read()
            cv2.imshow("img", self.img)
            cv2.waitKey(-1)
        cv2.waitKey(0)

    def __mouseHandler(self, event, x, y, flags, params):
        _, self.img = self.cam.read()
        if event == cv.CV_EVENT_LBUTTONDOWN and not self.mouse_drag:
            self.mouse_p1 = (x, y)
            self.mouse_drag = True
        elif event == cv.CV_EVENT_MOUSEMOVE and self.mouse_drag:
            cv2.rectangle(self.img, self.mouse_p1, (x, y), (255, 0, 0), 1, 8, 0)
        elif event == cv.CV_EVENT_LBUTTONUP and self.mouse_drag:
            self.mouse_p2 = (x, y)
            self.mouse_drag=False
        cv2.imshow("img",self.img)
        cv2.waitKey(-1)
        if self.mouse_p1 and self.mouse_p2:
            cv2.destroyWindow("img")
            xmax = max((self.mouse_p1[0],self.mouse_p2[0]))
            xmin = min((self.mouse_p1[0],self.mouse_p2[0]))
            ymax = max((self.mouse_p1[1],self.mouse_p2[1]))
            ymin = min((self.mouse_p1[1],self.mouse_p2[1]))
            self.bb = (xmin,ymin,xmax-xmin,ymax-ymin)
            self.camshift()

    def camshift(self):
        self.imgs=[]
        while True:
            try:
                hsv = cv2.cvtColor(self.img, cv.CV_BGR2RGB)
                mask = cv2.inRange(hsv, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
                x0, y0, w, h = self.bb
                x1 = x0 + w -1
                y1 = y0 + h -1
                hsv_roi = hsv[y0:y1, x0:x1]
                mask_roi = mask[y0:y1, x0:x1]
                hist = cv2.calcHist( [hsv_roi], [0], mask_roi, [16], [0, 180] )

                cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX);

                hist_flat = hist.reshape(-1)
                print hist
                self.imgs.append(hsv)
                prob = cv2.calcBackProject(self.imgs, [0], hist_flat, [0, 180], 1)
                prob &= mask
                term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )
                self.ellipse, self.bb = cv2.CamShift(prob, self.bb, term_crit)
                cv2.rectangle(self.img, (self.bb[0], self.bb[1]), (self.bb[0]+self.bb[2], self.bb[1]+self.bb[3]), color=(255,0,0))
                cv2.imshow("CAMShift", self.img)
                k = cv2.waitKey(20)
                if k==27:
                    cv2.destroyAllWindows()
                    break
                if k==114:
                    cv2.destroyAllWindows()
                    self.start()
                    break
                _, self.img = self.cam.read()
            except KeyboardInterrupt:
                cv2.destroyAllWindows()
                break

c = CAMShift(source='camshift_sample.avi')
#c = CAMShift(
#    source='/data/sleepysnail/task-output/ConcatenateVideoChunks/ConcatenateVideoChunks-data_sleepysnail_raw_20140425-175349_0-300-5.33b03a1e342900c570fac73900e54f89.avi')



#c = CAMShift()
#
# import numpy as np
# import cv2
# import cv
#
# cap = cv2.VideoCapture('camshift_sample.avi')
#
# # take first frame of the video
# ret,frame = cap.read()
# frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#
# # setup initial location of window
# r,h,c,w = 15,50,270,50  # simply hardcoded the values
# track_window = (c,r,w,h)
#
# # set up the ROI for tracking
# roi = frame[r:r+h, c:c+w]
#
#
# mask = cv2.inRange(roi, np.array(0), np.array(255))
# mask = np.ones(roi.shape, dtype=np.uint8)
# #roi_hist = cv2.calcHist([roi],[0], mask ,[10],[0,10])
# roi_hist, bins = np.histogram(roi, 20, [0, 255])
# roi_hist = roi_hist.astype(np.uint8)
#
#
# print roi_hist
# cv2.normalize(roi_hist, roi_hist,0,255,cv2.NORM_MINMAX)
# print roi_hist
#
# # Setup the termination criteria, either 10 iteration or move by atleast 1 pt
# term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )
#
# while True:
#     ret, frame = cap.read()
#
#     if ret:
#
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         print roi_hist
#         dst = cv2.calcBackProject([frame], [0], roi_hist, [0,255], 1.0)
#         print "~~~~~~~~~~~~~~~~~~~~~~~~~~#"
#         print dst
#
#         # apply meanshift to get the new location
#         ret, track_window = cv2.CamShift(dst, track_window, term_crit)
#
#         # Draw it on image
#
#         pts = cv.BoxPoints(ret)
#         pts = np.int0(pts)
#
#         img2 = np.copy(frame)
#
#         for p in pts:
#             cv2.circle(img2, tuple(p), 3, (255, 33, 166), -1)
#
#
#         cv2.imshow('img2',img2)
#
#         k = cv2.waitKey(1000) & 0xff
#         if k == 27:
#             break
#         else:
#             cv2.imwrite(chr(k)+".jpg", img2)
#
#     else:
#         break
#
# cv2.destroyAllWindows()
# cap.release()