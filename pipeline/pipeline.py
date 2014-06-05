__author__ = 'quentin'
import luigi
import numpy as np
from sleepysnail.pipes.tasks import *
from sleepysnail.preprocessing.roi_splitter import ROISplitter
from sleepysnail.preprocessing.undistortor import Undistortor
from sleepysnail.processing.blob_finder import Tracker


#1 fpm
SPEED_UP = 60*5


class MakeOneCsvPerROI(VideoToCsvTask):
    roi_id = luigi.IntParameter()
    r = luigi.FloatParameter(default=1.4)
    save_video_log = luigi.BooleanParameter(default=True)
    blob_finder = None
    #background_classif = cv2.NormalBayesClassifier()

    def requires(self):
        return [MakeVideoForRoi(videos=self.videos, roi_id=self.roi_id)]
    def _process(self, image):
        if self.blob_finder is None:
            self.blob_finder = Tracker(self.padding)

        log, line = self.blob_finder(image)

        f = str(self.capture.frame_number)
        id = str(self.roi_id)
        if line:
            out = ",".join([id, f, line])

        return log, out

    def _header(self):
        if self.blob_finder is None:
            self.blob_finder = Tracker(self.r)

        return "id, " + "frame, " + self.blob_finder.header()


class UndistortVideo(VideoToVideoTask):

    undistortor = None
    def requires(self):
        return [StretchHistogram(videos=self.videos)]

    def _process(self, image):
        if self.undistortor is None:
            self.undistortor = Undistortor(image)
        return self.undistortor.undistort(image)


class MakeVideoForRoi(VideoToVideoTask):
    roi_id = luigi.IntParameter()
    roi_splitter = None
    def requires(self):
        return [UndistortVideo(videos=self.videos)]

    def _process(self, image):
        if self.roi_splitter is None:
            self.roi_splitter = ROISplitter(image)
        return self.roi_splitter.split(image, self.roi_id)


class StretchHistogram(VideoToVideoTask):
    new_median=128.0

    undistortor = None
    def requires(self):
        return [ConcatenateVideoChunks(videos=self.videos, speed_up=SPEED_UP)]


    def _process(self, image):
        array = image.astype(np.float)
        med = np.median(array )
        array  = (array  * self.new_median) / med
        array  = np.where(array > 255, 255, array )
        #print array
        return array.astype(np.uint8)


class ConcatenateVideoChunks(VideoToVideoTask):
    def _process(self, image):
        return image


class HistSummary(VideoToCsvTask):
    def requires(self):
        return [ConcatenateVideoChunks(videos=self.videos, speed_up=SPEED_UP)]

    def _header(self):
        return "frame, median, q1, q3"

    def _process(self, image):
        m, q1, q3 =  np.percentile(image, [50, 25, 75])
        return None, "%i,%f, %f, %f" % (self.capture.frame_number,m , q1, q3)

class DayNight(TaskBase):
    videos = luigi.Parameter(default="")

    def requires(self):
        return [HistSummary(videos=self.videos)]

    def _header(self):
        return "is_day"

    @property
    def _file_extension(self):
        return ".csv"

    def run(self):

        input_files = self.input()
        with self.output().open('w') as f:

            data = np.genfromtxt(input_files[0].path, delimiter=',')
            print data
            data = (data[1:,1:]).astype(np.float32)

            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labs_masked, centre = cv2.kmeans(data, 2, criteria, 10, cv2.KMEANS_PP_CENTERS)


            day_idx = np.argmax(centre[[0,1], [0,0]])

            f.write(self._header() + "\n" )
            for l in labs_masked.flatten():
                if l == day_idx:
                    is_day = 1
                else:
                    is_day = 0
                f.write("%i\n" % is_day)


class MergeCSVs(TaskBase):
    videos = luigi.Parameter(default="")
    n_rois = luigi.IntParameter(default=18)

    def requires(self):
        return [MakeOneCsvPerROI(videos=self.videos, roi_id=i, save_video_log=True)
                for i in range(self.n_rois)]


    @property
    def _file_extension(self):
        return ".csv"

    def run(self):
        input_files = self.input()
        with self.output().open('w') as f:
            for i, infile in enumerate(input_files):
                for j, l in enumerate(infile.open()):
                    if i == 0 or j > 0:
                        f.write(l)

class MainTask(MainTaskBase):
    videos = luigi.Parameter(default="")
    def requires(self):
        prerequisites = [MergeCSVs(videos=self.videos), DayNight(videos=self.videos)]
        return prerequisites


class MasterTask(MainTaskBase):

    experiments = [
                   "/data/sleepysnail/raw/20140425-175349_0/",
                   "/data/sleepysnail/raw/20140502-175216_0",
                   "/data/sleepysnail/raw/20140516-173616_0",
                   "/data/sleepysnail/raw/20140516-173617_2"
                   ]

    def requires(self):
        prerequisites = [MainTask(videos=e) for e in self.experiments]
        return prerequisites

class TestTask(MainTaskBase):
    videos = luigi.Parameter(default="/data/sleepysnail/raw/20140425-175349_0/")
    def requires(self):
        prerequisites = [ConcatenateVideoChunks(videos=self.videos, speed_up=SPEED_UP)
        for i in range(1)]

        return prerequisites
class TestTask2(MainTaskBase):
    videos = luigi.Parameter(default="/data/sleepysnail/raw/20140425-175349_0/")
    def requires(self):
        prerequisites = [MakeVideoForRoi(videos=self.videos, roi_id="0")]

        return prerequisites


if __name__ == '__main__':
    luigi.run(main_task_cls=MasterTask)
    #luigi.run(main_task_cls=TestTask2)
