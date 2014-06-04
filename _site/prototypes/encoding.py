import sleepysnail 
from sleepysnail import VideoSink
import numpy as np


vsnk = VideoSink('mymovie.avi',size=(1000,500),colorspace='y8',rate=1, codec_family='lavc')
for i in range(1000):
    f = np.random.random_integers(0,255,size=[1000,500]).astype('uint8')
    vsnk(f)
    print i
vsnk.close()
