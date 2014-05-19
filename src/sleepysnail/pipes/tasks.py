import re
import datetime
import os
import luigi
import cv
import cv2
import dis
import inspect
import hashlib
from sleepysnail.utils.logger import Logger

from sleepysnail.acquisition.video_capture import VideoDirCapture, VIDEO_FORMAT
import operator


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

        # this is to force re-runing tasks when code has changed

        #print "--------------------------"
        #print self.__class__.__name__
        #print self.get_all_deps()

#            exit()
        self._class_code_hash = self.make_hash()
        self.delete_obsolete_targets()

    def get_all_deps(self):
        all_deps = []
        for x in self.requires():
            cname = x.__class__.__name__
            all_deps.append(cname)
            all_deps += x.get_all_deps()
        out = []
        for i in all_deps:
            if i not in out:
                out.append(i)

        return out

    def make_hash(self):
        class_descr = ";".join(inspect.getsourcelines(self.__class__)[0])
        return hashlib.md5(str(class_descr)).hexdigest()



    def delete_obsolete_targets(self):
        #check class hash, delete old files
        class_output_dir = os.path.join(OUTPUT_DIR, self.__class__.__name__)
        if not os.path.isdir(class_output_dir):
            return

        file_names = os.listdir(class_output_dir)
        for f in file_names:
            f_hash = f.split(".")[1]
            #delete file if class code has changed
            if f_hash != self._class_code_hash:
                os.remove( os.path.join(OUTPUT_DIR, self.__class__.__name__,f))
                Logger.info("The source code for this task has changed.\n"
                            "Removing opsolete target: \n"
                            "old hash = {0}"
                            "new hash = {1}".format(f_hash, self._class_code_hash))





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

            filename = '{0}-{1}.{2}{3}'.format(class_, params_str, self._class_code_hash , self._file_extension)

        if not self.use_human_readable_filenames or len(filename) > self._FILENAME_LENGTH_LIMIT:
            params_str = hashlib.md5(';'.join(map(str, param_values))).hexdigest()
            filename = '{0}-{1}.{2}{3}'.format(class_, params_str, self._class_code_hash , self._file_extension)

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



class MainTaskBase(TaskBase):
    def __init__(self, *args, **kwargs):
        super(MainTaskBase, self).__init__(*args, **kwargs)
        Logger.info("VISUALISE AT \n"
                    "http://localhost:8082/static/visualiser/index.html#{0}%28%29".format(self.__class__.__name__))

    @property
    def _file_extension(self):
        return ".targets"

    def run(self):
        f = self.output().open('w')
        with self.output().open('w') as f:
            for infile in self.input():
                f.write(infile.path + "\n")





class VideoToVideoTask(TaskBase):

    videos = luigi.Parameter(default="")
    speed_up = luigi.IntParameter(default=1)
    out_fps = luigi.IntParameter(default=5)
    capture = None

    @property
    def _file_extension(self):
        return ".%s" % VIDEO_FORMAT['extension']

    def _process(self, image):
        raise NotImplementedError

    def run(self):
        try:

            f = self.output().open('w')
            f.close()

            # if an input is available we should get videos from the preceding task
            input_files = self.input()
            if len(input_files) == 1:
                video_file = input_files[0].path
            else:
                video_file = self.videos

            self.capture = VideoDirCapture(video_file, self.speed_up)
            video_writer = None

            for img in self.capture.read_all():
                img = self._process(img)
                if video_writer is None:
                    video_writer = cv2.VideoWriter(self.output().path,
                                                   fourcc=VIDEO_FORMAT['fourcc'],
                                                   fps=self.out_fps,
                                                   frameSize=(img.shape[1], img.shape[0]))


                try:
                    img = cv2.cvtColor(img, cv.CV_GRAY2BGR)
                finally:
                    video_writer.write(img)

        except KeyboardInterrupt:
            Logger.warning("Removing files")
            os.remove(self.filepath)



class VideoToCsvTask(TaskBase):
    videos = luigi.Parameter(default="")
    speed_up = luigi.IntParameter(default=1)
    save_video_log = luigi.BooleanParameter(default=False)
    capture = None

    @property
    def _file_extension(self):
        return ".csv"

    def _process(self, image):
        raise NotImplementedError

    def _header(self):
        raise NotImplementedError

    def tmp_log_video(self):
        import tempfile
        return os.path.join(tempfile.gettempdir(),
                            self._filename + '.' + VIDEO_FORMAT["extension"])
        # return os.path.join(tempfile.gettempdir(), "test.avi")
    def run(self):

        video_writer = None

        try:
            with self.output().open('w') as f:

                input_files = self.input()
                assert len(input_files) == 1
                video_file = input_files[0].path

                self.capture = VideoDirCapture(video_file, self.speed_up)

                f.write(self._header() + "\n" )
                for img in self.capture.read_all():
                    log, row = self._process(img)
                    if row is not None:
                        f.write(row + "\n")

                    if self.save_video_log:
                        if video_writer is None:
                            video_writer = cv2.VideoWriter(self.tmp_log_video(),
                                                   fourcc=VIDEO_FORMAT['fourcc'],
                                                   fps=5,
                                                   frameSize=(log.shape[1], log.shape[0]))
                        try:
                            log = cv2.cvtColor(log, cv.CV_GRAY2BGR)
                        finally:
                            video_writer.write(log)

        except KeyboardInterrupt:
            Logger.warning("Removing files")
            os.remove(self.filepath)