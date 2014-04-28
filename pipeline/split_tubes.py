__author__ = 'quentin'
import luigi
from sleepysnail.pipes.tasks import VideoToVideoTask, MainTaskBase
from sleepysnail.preprocessing.roi_splitter import ROISplitter

class ConcatenateVideoChunks(VideoToVideoTask):
    #dm
    def _process(self, image):
        return image

class MakeVideoForRoi(VideoToVideoTask):
    roi_id = luigi.IntParameter()
    roi_splitter = None
    def requires(self):
        return [ConcatenateVideoChunks(videos=self.videos, speed_up=60*5)]

    def _process(self, image):
        if self.roi_splitter is None:
            self.roi_splitter = ROISplitter(image)
        return self.roi_splitter.split(image,self.roi_id)

class MainTask(MainTaskBase):

    def requires(self):
        return [
            MakeVideoForRoi(videos="/data/sleepysnail/raw/20140425-175349_0/", roi_id=i)
            for i in range(18)]
            #ConcatenateVideoChunks(videos="/data/sleepysnail/raw/20140425-175349_0/", speed_up=60*5)]


if __name__ == '__main__':
    luigi.run(main_task_cls=MainTask)