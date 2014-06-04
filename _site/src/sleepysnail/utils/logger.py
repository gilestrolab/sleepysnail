__author__ = 'quentin'


class Logger:
    def __init__(self):
        pass
    @classmethod
    def info(self, str):
        print str
    #todo use stderr
    @classmethod
    def warning(self, str):
        print str
    @classmethod
    def error(self, str):
        print str
