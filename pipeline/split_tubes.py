__author__ = 'quentin'
import luigi
import numpy as np
from sleepysnail.pipes.tasks import *
from sleepysnail.preprocessing.roi_splitter import ROISplitter

class MakeOneCsvPerROI(VideoToCsvTask):
    roi_id = luigi.IntParameter()
    padding = luigi.IntParameter(default=25)



    def requires(self):
        return [MakeVideoForRoi(videos=self.videos, roi_id=self.roi_id)]
    def _header(self):
        return "id, f, x, y, area"


    def filter_good_contours(self, contour, min_length=50, max_length=200, min_ar=1, max_ar=3):
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

    def _process(self, image):
        padding = self.padding

        frame = cv2.GaussianBlur(image , (9,9), 1.5)

        blur_frame = cv2.blur(frame, (151,151))
        blur_frame = np.pad(blur_frame, padding, "edge")

        blur_frame[padding:-padding, padding :-padding ] = frame

        med = cv2.medianBlur(blur_frame, 15)
        morph = cv2.dilate(med, np.ones((3, 3), dtype=np.uint8), iterations=4)
        morph = cv2.erode(morph, np.ones((3, 3), dtype=np.uint8), iterations=4)

        binary = cv2.adaptiveThreshold(morph, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, 7)
        binary = cv2.dilate(binary, np.ones((3,3), dtype=np.uint8), iterations=7)

        orig_bin = cv2.adaptiveThreshold(blur_frame, 255,  cv.CV_ADAPTIVE_THRESH_GAUSSIAN_C, cv.CV_THRESH_BINARY_INV, 151, -5)
        orig_bin = cv2.dilate(orig_bin, np.ones((3,3), dtype=np.uint8), iterations=2)

        binary = cv2.bitwise_and(orig_bin, binary)
        binary = binary[padding :-padding ,padding :-padding ]
        contours, hiera = cv2.findContours(binary, cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)

        contours = filter(self.filter_good_contours, contours)
        contours = [cv2.approxPolyDP(c, 1, True) for c in contours]
        if len(contours) == 1:
            f = self.capture.frame_number
            mom= cv2.moments(contours[0], False)
            id = self.roi_id
            zeroth = mom["m00"]
            x = mom["m10"] / zeroth
            y = mom["m01"] / zeroth
            area = zeroth
            features = (id, f, x, y, area)
            out = ",".join(str(i) for i in features)
            return out





class MakeVideoForRoi(VideoToVideoTask):
    roi_id = luigi.IntParameter()
    roi_splitter = None
    def requires(self):
        return [ConcatenateVideoChunks(videos=self.videos, speed_up=60*5)]

    def _process(self, image):
        if self.roi_splitter is None:
            self.roi_splitter = ROISplitter(image)
        return self.roi_splitter.split(image, self.roi_id)





class ConcatenateVideoChunks(VideoToVideoTask):
    def _process(self, image):
        return image

class MainTask(MainTaskBase):

    def requires(self):
        return [
            MakeOneCsvPerROI(videos="/data/sleepysnail/raw/20140425-175349_0/", roi_id=i)
            for i in range(18)]

            #ConcatenateVideoChunks(videos="/data/sleepysnail/raw/20140425-175349_0/", speed_up=60*5)]


if __name__ == '__main__':
    luigi.run(main_task_cls=MainTask)