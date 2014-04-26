__author__ = 'quentin'

import re
import datetime
import os
import luigi
import cv
import cv2

from sleepysnail.acquisition.video_capture import VideoDirCapture, VIDEO_FORMAT


# Allow getting the output directory from [output] > directory in config file
OUTPUT_DIR = luigi.configuration.get_config().get('output', 'directory', 'task-output')


def filesafe_string(original_filename):
    """
Replaces all non ascii or non-digit characters
:param original_filename: Original string replace
:return: version of the original_filename that is safe as a filename
"""
    original_filename = str(original_filename)
    # Based on http://stackoverflow.com/a/295466/171400
    # change all non-safe symbols to _
    original_filename = re.sub(r'[^\d\w.-]', '_', original_filename)
    # Change multiple spaces to single space
    original_filename = re.sub(r'_+', '_', original_filename)
    # Remove spaces at the start and end of the string
    original_filename = original_filename.strip('_')
    return original_filename

class TaskBase(luigi.Task):

    _FILENAME_LENGTH_LIMIT = 200
    """Maximum supported length for filenames. Hashed filenames will be used instead of human-readable ones if
    the length goes above that. This needs to be a bit lower, as luigi appends some temp extension while saving files
    """

    use_human_readable_filenames = True
    """
    If set to true, human-readable filenames will try to be generated,
    otherwise, the parameter string will be shortened using md5. A clash is less likely, if non-human readable filenames
    used
    """

    def __init__(self, *args, **kwargs):
        super(TaskBase, self).__init__(*args, **kwargs)

    @property
    def _file_extension(self):
        """
        The file extension for the serialised objects to use.

        :return: the file extension, including the dot in front of it. i.e. ``.pickle``
        """
        return ''

    @property
    def _filename(self):
        """
Method that generates the filename of the class.
This defaults to the class name, followed by dash-separated parameters of the class followed by
:attr:`TaskBase._file_extension`

:return: The generated filename
:rtype: str
"""
        try:
            return self.__filename
        except AttributeError:
            pass

        # Default filename that just lists class name and parameters in dashes
        class_ = self.__class__.__name__
        filename = ''

        params = self.get_params()
        param_values = [getattr(self, x[0]) for x in params if x[1].significant]

        if self.use_human_readable_filenames:
            params_str = '-'.join(map(filesafe_string, param_values))
            if params_str:
                params_str = ''.join(['-', params_str])

            params_str = params_str.strip('-')

            filename = '{0}-{1}{2}'.format(class_, params_str, self._file_extension)

        if not self.use_human_readable_filenames or len(filename) > self._FILENAME_LENGTH_LIMIT:
            import hashlib
            params_str = hashlib.md5(';'.join(map(str, param_values))).hexdigest()
            filename = '{0}-{1}{2}'.format(class_, params_str, self._file_extension)

        assert(filename != '')
        # Cache the filename before returning, especially important for the hashlib generated ones
        self.__filename = filename

        return filename




    def _output(self):
        output = luigi.File(self.filepath)
        return output
        #raise NotImplementedError

    def output(self):
        """
Returns the output of the class.
Ensures we only have one instance of the output object, meaning we have only one cache per output object.

Please do not override this in your class, and override :meth:`TaskBase._output()` instead.

:return: Cached result of :meth:`TaskBase._output()`
"""
        try:
            # Make sure we have only one instance of output object
            return self.__output
        except AttributeError:
            output = self._output()
            self.__output = output
            return output

    @property
    def filepath(self):
        """
Generates the filepath of the task, default is of format ``<OUTPUT_DIR>/<CLASS>/<FILENAME>``
where ``<FILENAME>`` is defined in :attr:`TaskBase._filename`.

:return:
"""
        # Force the directory structure <OUTPUT_DIR>/<CLASS>/<FILENAME>
        return os.path.join(OUTPUT_DIR,
                            self.__class__.__name__,
                            self._filename)





class VideoToVideoTask(TaskBase):

    video_dir = luigi.Parameter(default = "/data/sleepysnail/raw/20140425-175349_0/")
    speed_up = luigi.IntParameter(default=100)
    out_fps = luigi.IntParameter(default=30)

    @property
    def _file_extension(self):
        return ".%s" % VIDEO_FORMAT['extension']

    def run(self):
        f = self.output().open('w')
        f.close()

        capture = VideoDirCapture(self.video_dir, self.speed_up)
        video_writer = None

        for img in capture.read_all():
            if video_writer is None:
                video_writer = cv2.VideoWriter(self.output().path,
                                               fourcc=VIDEO_FORMAT['fourcc'],
                                               fps=self.out_fps,
                                               frameSize=(img.shape[1], img.shape[0]))

            try:
                img = cv2.cvtColor(img, cv.CV_GRAY2BGR)
            finally:
                video_writer.write(img)

if __name__ == '__main__':
    luigi.run(main_task_cls=VideoToVideoTask)