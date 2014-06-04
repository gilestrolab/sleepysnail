__author__ = 'quentin'

import cv2
import cv
import numpy as np
import scipy.optimize


from sleepysnail.utils.logger import Logger
class Undistortor(object):
    def __init__(self, image):
        # preprocess image
        erosion_size=9
        kern_size = 2*erosion_size + 1
        elem = cv2.getStructuringElement( cv2.MORPH_ELLIPSE, (kern_size, kern_size),(erosion_size, erosion_size))
        grey = cv2.medianBlur(image,3)
        morph = cv2.dilate(grey, elem)
        morph = cv2.erode(morph, elem)
        morph = cv2.subtract(morph, grey)
        p = np.percentile(morph,90)

        _,morph = cv2.threshold(morph,p,255,cv.CV_THRESH_BINARY)

        rranges = (slice(4000, 6000, 500), slice(0, -7, -0.5))
        res = scipy.optimize.brute(self.distance_fun, rranges,args=(morph,),finish=scipy.optimize.fmin)
        #print scipy.optimize.fmin(self.distance_fun, [5000,-3],args=(image,))
        self.cam_mat, self.coefs = self._find_cam_matrix(image, *res)


    def distance_fun(self,x , *args):

        f,k = x

        morph = args[0]


        cam_mat, coefs = self._find_cam_matrix(morph, f, k)
        tmp = cv2.undistort(morph, cam_mat, coefs)
        lines = cv2.HoughLinesP(tmp, rho=1, theta=np.pi/180.0, threshold=10, minLineLength=morph.shape[0]/1.5)
        #pl.imshow(tmp)

        if lines is None:
            return np.Inf

        else:
            # Logger.info(str([f,k,lines.shape[1]]))

            # print "linesssssssssssssssss"
            # print lines
            # print lines.shape
            pt1 = lines[0,:, 0] + 1j * lines[0, :, 1]
            pt2 = lines[0, :, 2] + 1j * lines[0, :, 3]
            out = 1 / np.sum(abs(pt1 - pt2))
            return out

    def _find_cam_matrix(self, image,f,k):
        camera_matrix = np.zeros((3,3),'float32')
        camera_matrix[0,0]= f
        camera_matrix[1,1]= f
        camera_matrix[2,2]=1.0
        camera_matrix[0,2]=image.shape[1]/2.0
        camera_matrix[1,2]=image.shape[0]/2.0
        dist_coefs = np.array([k,k,0,0],'float32')
        return camera_matrix, dist_coefs


    def undistort(self, image):
        cam_mat=self.cam_mat
        coefs=self.coefs
        return cv2.undistort(image, cam_mat, coefs)
