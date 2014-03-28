__author__ = 'quentin'

import cv2
import cv
import os
import numpy as np

from sleepysnail.utils.logger import Logger
#import matplotlib.animation as animation


VIDEO_CHUNK_SIZE = 100
MAX_CAM_NUMBER = 1
#VIDEO_FORMAT = cv.CV_FOURCC('D', 'I', 'V', 'X')
#VIDEO_FORMAT = cv.CV_FOURCC('M','J','P','G')
VIDEO_FORMAT = cv.CV_FOURCC('H','2','6','4')


FPS = 5

class AutoCaptureCollection(list):
    def __init__(self, out_dir):
        super(AutoCaptureCollection, self).__init__()



        for i in range(MAX_CAM_NUMBER):

            try:
                Logger.info("Probing camera #{0}".format(i))
                cap = AutoVideoCapture(i, out_dir)
                self.append(cap)

            except Exception as e:
                print e
                pass

        Logger.info("Managed to open {0} cameras".format(len(self)))
        print self




class AutoVideoCapture(object):
    def __init__(self, idx, out_dir):

        #super(AutoVideoCapture, self).__init__(device=idx)
        self.stream = cv2.VideoCapture(device=idx)

        if not self.stream.isOpened():
            raise Exception("cannot open this camera")
            #try to get the first frame
            ret,frame = self.stream.read()
            print  "-------------"
            print frame
            if not ret or frame.empty():
                raise Exception("Camera opens but does not manage to read frame")






        self.idx = idx
        self.name = str(idx)
        self.frame_count = 0
        self.is_started = False
        self.video_writer = None
        self.out_dir = out_dir

    def start(self):
        if  self.is_started:
            return

        self.is_started = True
        # todo set name?
        out_dirpath = self.out_dir +"/"+ self.name
        if not os.path.exists(out_dirpath):
            os.makedirs(out_dirpath)
        else:
            raise Exception("{0} Exists already".format(out_dirpath))




    def read(self):
        ret,frame = self.stream.read()
        self.frame_size = frame.shape[:2]
        print self.frame_size
        if ret:
            cv2.imshow(self.name, frame)
            return frame
        else:
            return None


    def _write_to_file(self, frame):

        if self.frame_count % VIDEO_CHUNK_SIZE == 0:

            self.frame_count / VIDEO_CHUNK_SIZE
            out_filename = self.out_dir +"/"+ self.name + "/{0}_{1}.avi".format(self.name,
                                                                     self.frame_count / VIDEO_CHUNK_SIZE)
            try:
                self.video_writer.close()
            except:
                pass

            self.video_writer = cv2.VideoWriter(out_filename, VIDEO_FORMAT, FPS, self.frame_size, True)
            print out_filename, VIDEO_FORMAT, FPS, self.frame_size

        assert(self.video_writer.isOpened())

        self.video_writer.write(frame)
        print frame.shape, self.video_writer

    def capture(self):
        frame = self.read()

        if not self.is_started:
            return

        if frame is not None:

            self._write_to_file(frame)
            self.frame_count += 1







