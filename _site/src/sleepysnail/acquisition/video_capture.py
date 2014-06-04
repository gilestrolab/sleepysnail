__author__ = 'quentin'

import cv2
import numpy as np
import cv
import os
import time

from sleepysnail.utils.logger import Logger

from sleepysnail.acquisition.mencoder_wrappers import VideoSource

VIDEO_CHUNK_SIZE = 1e4
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
    def __del__(self):
        for i in self:
            del(i)

class AutoVideoCapture(object):
    def __init__(self, idx, raw_data_dir, fps):

        self.stream = cv2.VideoCapture(device=idx)

        if not self.stream.isOpened():
            raise Exception("cannot open this camera")
            #try to get the first frame
        #~ ret,frame = self.stream.read()
        #~ if not ret or len(frame) == 0:
            #~ self.stream.release()
            #~ print frame
            #~ raise Exception("Camera opens but does not manage to read frame")
            
        self.idx = idx
        self.name = time.strftime("%Y%m%d-%H%M%S_") + str(self.idx)
        self.fps = fps
        self.frame_count = 0
        self.is_started = False
        self.video_writer = None
        self.raw_data_dir = raw_data_dir
        self.frame_size = None
        self.out_dirpath = None

    def start(self):
        if self.is_started:
            return

        self.is_started = True
        cv2.destroyWindow(self.name)
        self.name = time.strftime("%Y%m%d-%H%M%S_") + str(self.idx)
        self.out_dirpath = self.raw_data_dir +"/"+ self.name

        if not os.path.exists(self.out_dirpath):
            os.makedirs(self.out_dirpath)
            Logger.info("Start recording in " + self.out_dirpath)
        else:
            raise Exception("{0} Exists already".format(self.out_dirpath))


    def read(self):
        ret, frame = self.stream.read(True)
        
        if frame is None:
            return None

        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv.CV_GRAY2BGR)

        self.frame_size = frame.shape[1], frame.shape[0]

        if ret:
            display = np.copy(frame)

            orig = display.shape[1]/8, display.shape[0]/8
            if self.is_started:
                text = "RECORDING, chunk #{0} !!".format(int(self.frame_count / VIDEO_CHUNK_SIZE))
            else:
                text = "Press SPACE BAR to start recording!"
            cv2.putText(display, text, orig,  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), thickness=2, lineType=cv.CV_AA)
            cv2.imshow(self.name, display)
            return frame
        else:
            return None


    def _write_to_file(self, frame):

        if self.frame_count % VIDEO_CHUNK_SIZE == 0:
            out_filename = self.out_dirpath + "/{0}_{1}.{2}".format(
                self.name,
                str(int(self.frame_count / VIDEO_CHUNK_SIZE)).zfill(3),
                VIDEO_FORMAT["extension"])

            Logger.info("Device \"{0}\" Making new video chunk: {1}".format(self.name, out_filename))
        
            self.video_writer = cv2.VideoWriter(out_filename, VIDEO_FORMAT["fourcc"], self.fps, self.frame_size)
            
        assert(self.video_writer.isOpened())

        self.video_writer.write(frame)

    def capture(self):
        frame = self.read()

        if not self.is_started:
            return

        if frame is not None:
            self._write_to_file(frame)
            self.frame_count += 1

    def __del__(self):
        self.stream.release()



class VideoDirCapture(object):
    """
Capture wrapper for a directory containing sorted files
"""
    def __init__(self, videos, keep_every=1):
        if os.path.isdir(videos):
            self.__file_list = [os.path.join(videos,f) for f in os.listdir(videos) if f.endswith(".avi")]
            if len(self.__file_list) < 1:
                raise Exception("the directory does not contain avi files")
            self.__file_list = [f for f in reversed(sorted(self.__file_list))]
        else:
            self.__file_list = [videos]

        self.__current_capture = cv2.VideoCapture(self.__file_list.pop())
        self.__frame_number = 0
        self.__keep_every = keep_every

    @property
    def frame_number(self):
        return self.__frame_number

    def read(self):
        if self.__keep_every != 1:
            capt_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_POS_FRAMES)
            total_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_FRAME_COUNT)
            next_frame_n = capt_frame_n + self.__keep_every - 1
            if next_frame_n > total_frame_n:
                if len(self.__file_list) == 0:
                    return None
                self.__current_capture = cv2.VideoCapture(self.__file_list.pop())
                Logger.info("Merging next chunk. %i chunks to go" % len(self.__file_list))
                next_frame_n %= self.__keep_every
                total_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_FRAME_COUNT)
                if not next_frame_n or total_frame_n < next_frame_n:
                    return None

            self.__current_capture.set(cv.CV_CAP_PROP_POS_FRAMES, next_frame_n)

        _, image = self.__current_capture.read()


        try:
            image = cv2.cvtColor(image, cv.CV_BGR2GRAY)
        except:
            pass
        self.__frame_number += 1

        return image

    def read_all(self):
        while True:
            image = self.read()
            if image is None:
                break
            yield image




#
# class VideoDirCapture(object):
#     """
#     Capture wrapper for a directory containing sorted files
#     """
#     def __init__(self, videos, keep_every=1):
#         if os.path.isdir(videos):
#             self.__file_list = [os.path.join(videos,f) for f in os.listdir(videos) if f.endswith(".avi")]
#             if len(self.__file_list) < 1:
#                 raise Exception("the directory does not contain avi files")
#             self.__file_list = [f for f in reversed(sorted(self.__file_list))]
#         else:
#             self.__file_list = [videos]
#
#         self.__current_capture = cv2.VideoCapture(self.__file_list.pop())
#         self.__frame_number = 0
#         self.__keep_every = keep_every
#
#     @property
#     def frame_number(self):
#         return self.__frame_number
#
#     def read(self):
#
#         if self.__keep_every != 1:
#             capt_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_POS_FRAMES)
#             total_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_FRAME_COUNT)
#             next_frame_n = capt_frame_n + self.__keep_every - 1
#
#             if next_frame_n > total_frame_n:
#                 if len(self.__file_list) == 0:
#                     return None
#                 self.__current_capture = cv2.VideoCapture(self.__file_list.pop())
#                 print "?"
#                 Logger.info("Merging next chunk. %i chunks to go" % len(self.__file_list))
#                 next_frame_n %= self.__keep_every
#                 total_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_FRAME_COUNT)
#                 if not next_frame_n or total_frame_n < next_frame_n:
#                     return None
#
#             self.__current_capture.set(cv.CV_CAP_PROP_POS_FRAMES, next_frame_n)
#
#         _, image = self.__current_capture.read()
#
#
#         try:
#             image = cv2.cvtColor(image, cv.CV_BGR2GRAY)
#         except:
#             pass
#         self.__frame_number += 1
#
#         return image
#
#     def read_all(self):
#         while True:
#             image = self.read()
#             if image is None:
#                 break
#             yield image


# class VideoDirCaptureMencoder(VideoDirCapture):
#     """
#     Capture wrapper for a directory containing sorted files
#     """
#     def __init__(self, videos, keep_every=1):
#         if os.path.isdir(videos):
#             self.__file_list = [os.path.join(videos,f) for f in os.listdir(videos) if f.endswith(".avi")]
#             if len(self.__file_list) < 1:
#                 raise Exception("the directory does not contain avi files")
#             self.__file_list = [f for f in reversed(sorted(self.__file_list))]
#         else:
#             self.__file_list = [videos]
#
#         self.guessed_colorspace
#         self.__current_capture = cv2.VideoCapture(self.__file_list.pop())
#         self.__frame_number = 0
#         self.__keep_every = keep_every
#
#
#     def read(self):
#         if self.__keep_every != 1:
#             capt_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_POS_FRAMES)
#             total_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_FRAME_COUNT)
#             next_frame_n = capt_frame_n + self.__keep_every - 1
#
#             if next_frame_n > total_frame_n:
#                 if len(self.__file_list) == 0:
#                     return None
#                 self.__current_capture = VideoSource(self.__file_list.pop(),colorspace=self.guessed_colorspace)
#                 Logger.info("Merging next chunk. %i chunks to go" % len(self.__file_list))
#                 next_frame_n %= self.__keep_every
#                 total_frame_n = self.__current_capture.get(cv.CV_CAP_PROP_FRAME_COUNT)
#                 if not next_frame_n or total_frame_n < next_frame_n:
#                     return None
#
#             self.__current_capture.set(cv.CV_CAP_PROP_POS_FRAMES, next_frame_n)
#
#         _, image = self.__current_capture.read()
#
#
#         try:
#             image = cv2.cvtColor(image, cv.CV_BGR2GRAY)
#         except:
#             pass
#         self.__frame_number += 1
#
#         return image
#
#
#
