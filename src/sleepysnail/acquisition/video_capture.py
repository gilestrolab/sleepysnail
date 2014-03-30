__author__ = 'quentin'

import cv2
import cv
import os
import numpy as np

from sleepysnail.utils.logger import Logger
#import matplotlib.animation as animation


VIDEO_CHUNK_SIZE = 1000
MAX_CAM_NUMBER = 10

VIDEO_FORMAT = {'fourcc':cv.CV_FOURCC('D', 'I', 'V', 'X'), 'extension':"avi"}


class AutoCaptureCollection(list):
    def __init__(self, out_dir, fps):
        super(AutoCaptureCollection, self).__init__()



        for i in range(MAX_CAM_NUMBER):

            try:
                Logger.info("Probing camera #{0}".format(i))
                cap = AutoVideoCapture(i, out_dir, fps)
                self.append(cap)

            except Exception as e:
                Logger.warning(e)
                pass

        Logger.info("Managed to open {0} cameras".format(len(self)))





class AutoVideoCapture(object):
    def __init__(self, idx, out_dir, fps):

        #super(AutoVideoCapture, self).__init__(device=idx)
        self.stream = cv2.VideoCapture(device=idx)

        if not self.stream.isOpened():
            raise Exception("cannot open this camera")
            #try to get the first frame
            ret,frame = self.stream.read()
            if not ret or frame.empty():
                raise Exception("Camera opens but does not manage to read frame")






        self.idx = idx
        self.name = str(idx)
        self.fps = fps
        self.frame_count = 0
        self.is_started = False
        self.video_writer = None
        self.out_dir = out_dir

    def start(self):
        if  self.is_started:
            return

        self.is_started = True
        
        out_dirpath = self.out_dir +"/"+ self.name
        if not os.path.exists(out_dirpath):
            os.makedirs(out_dirpath)
            Logger.info("Start recording in " + out_dirpath)
        else:
            raise Exception("{0} Exists already".format(out_dirpath))




    def read(self):
        ret,frame = self.stream.read(True)
        if frame is None:
			return None
        self.frame_size = frame.shape[1], frame.shape[0]
        if ret:
            cv2.imshow(self.name, frame)
            return frame
        else:
            return None


    def _write_to_file(self, frame):

        if self.frame_count % VIDEO_CHUNK_SIZE == 0:
			
            self.frame_count / VIDEO_CHUNK_SIZE
            out_filename = self.out_dir +"/"+ self.name + "/{0}_{1}.{2}".format(self.name,
                                                                     self.frame_count / VIDEO_CHUNK_SIZE, VIDEO_FORMAT["extension"])
                                                                     
            Logger.info("Device \"{0}\" Making new video chunk:{1}".format(self.name,out_filename))
			
            try:
                self.video_writer.close()
            except:
                pass


            self.video_writer = cv2.VideoWriter(out_filename, VIDEO_FORMAT["fourcc"], self.fps , self.frame_size)
            
        print self.frame_size
        assert(self.video_writer.isOpened())

        self.video_writer.write(frame)

    def capture(self):
        frame = self.read()

        if not self.is_started:
            return

        if frame is not None:
            self._write_to_file(frame)
            self.frame_count += 1







