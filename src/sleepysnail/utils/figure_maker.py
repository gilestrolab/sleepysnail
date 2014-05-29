__author__ = 'quentin'

import cv
import cv2
import os

class FigureMaker(object):
    def __init__(self, prefix, name):
        self.prefix = prefix
        self.name = name
        self.counter = 0
        if not os.path.exists(self.prefix):
            os.makedirs(self.prefix)

    def __call__(self, figure, counter=None):
        if not counter:
            self.counter += 1
            file_name = "%s_%04d.png" % (self.name, self.counter)
        else:
            file_name = "%s_%s.png" % (self.name, counter)



        path = os.path.join(self.prefix, file_name)

        cv2.imwrite(path, figure)
