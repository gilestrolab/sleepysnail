__author__ = 'quentin'

import cv2
import cv
import numpy as np
import itertools


class ROISplitter(object):
    def __init__(self, image, grid_size=(10,4)):
        np.random.seed(0)
        self.angle_count = 0
        corners = self.show_corners(image)
        decimated = self.decimate(corners)
        theo_points, teta = self.find_grid(decimated)
        all_rois = self.make_all_rois(theo_points, teta, grid_size)
        self.all_rois = self.filter_rois(all_rois)

        # theo_points, teta = self.find_grid(decimated)
        #
        # #
        # # corners2 = cv2.cvtColor(image, cv.CV_GRAY2BGR)
        # # for (x,y) in theo_points:
        # #     cv2.circle(corners2, (int(x),int(y)), 8, (0,255,255), -1, cv.CV_AA)
        # #     cv2.circle(corners2, (int(x),int(y)), 8, (255,0,0), 3, cv.CV_AA)
        # # cv2.imshow("test", corners2)
        # # cv2.waitKey(-1)
    @property
    def nrois(self):
        return len(self.all_rois)

    def make_all_rois(self, theo_points, teta, grid_size):
        nrows = (grid_size[0] - 1)
        ncols = (grid_size[1] - 1)
        n_rois = nrows *  ncols

        all_rois = [self.get_roi(r, theo_points, teta) for r in range(n_rois)]

        order = np.arange(n_rois).reshape((ncols, nrows)).T.flatten()

        return [all_rois[i] for i in order]




    def filter_rois(self, all_rois, min_ar=3):
        out = [(t,m,size) for t,m,size in all_rois if size[0] /float(size[1]) > min_ar]
        return out


    def split(self, image, which):
        which = int(which)
        (box_a,box_b,box_c,box_d), rotat_mat,  size = self.all_rois[which]
        roi_rec = image[box_a:box_b, box_c:box_d]
        roi = cv2.warpAffine(roi_rec, rotat_mat, size, flags=cv2.INTER_CUBIC)
        return roi



    def show_corners(self, image, erosion_size=5, percent_threshold=98):
        kern_size = 2*erosion_size + 1
        elem = cv2.getStructuringElement( cv2.MORPH_ELLIPSE, (kern_size, kern_size),(erosion_size, erosion_size))
        grey = cv2.medianBlur(image,3)
        morph = cv2.dilate(grey, elem)
        morph = cv2.erode(morph, elem)
        morph = cv2.subtract(morph, grey)
        corners = cv2.cornerHarris(morph, kern_size, kern_size, 1e-2)
        t = np.percentile(corners,percent_threshold)
        return corners > t

    def decimate(self, image, rate=0.8):
        rand = np.random.uniform(0,1,image.shape[0] * image.shape[1]).reshape(image.shape)
        decimated = image & (rand > rate)
        return decimated

    def distance_fun(self, points, teta, size=(10,4)):
        rotat_mat = self.make_rotation_mat(teta)
        pts = np.dot(points, rotat_mat.T).astype(np.float32)

        nrows=size[0]
        ncols=size[1]
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        compact_c, labels_c ,centres_c = cv2.kmeans(pts[:,0],ncols, criteria , 5, flags=cv2.KMEANS_PP_CENTERS)
        compact_r, labels_r ,centres_r = cv2.kmeans(pts[:,1],nrows, criteria , 5, flags=cv2.KMEANS_PP_CENTERS)

        uniq_labs_c = np.unique(labels_c)
        points_clusters = [pts[ (labels_c == lab).flatten() ,0] for lab in uniq_labs_c]
        medians_c = [np.median(pcl) for pcl in points_clusters]


        uniq_labs_r = np.unique(labels_r)
        points_clusters = [pts[(labels_r == lab).flatten(),1] for lab in uniq_labs_r]
        medians_r = [np.median(pcl) for pcl in points_clusters]


        return np.log10(compact_c) + np.log10(compact_r), medians_c, medians_r
   # centres_r.flatten()
        #return np.log10(compact_c) + np.log10(compact_r), centres_c.flatten(), centres_r.flatten()

    def make_rotation_mat(self, teta):
        return np.array([
                [np.cos(teta), -np.sin(teta)],
                [np.sin(teta), np.cos(teta)],
            ])


    def find_grid(self, image, size=(10,4), teta_resolution= .01):
        points = [(j,i) for (i,j), value in np.ndenumerate(image) if value]
        best_dist = np.Inf
        for teta in np.arange(-np.pi/4, np.pi/4, teta_resolution * np.pi):

            dist, centres_c, centres_r = self.distance_fun(points, teta)
            if dist < best_dist:
                best_dist = dist
                best_centres_c, best_centres_r = centres_c, centres_r
                invert_teta = -teta

        best_centres_r =  np.sort(best_centres_r)
        best_centres_c =  np.sort(best_centres_c)

        all_crosses = np.array([(c,r) for c, r in itertools.product(np.sort(best_centres_c),np.sort(best_centres_r))])
        invert_rotat_mat =  self.make_rotation_mat(invert_teta)
        theo_points = np.dot(all_crosses, invert_rotat_mat.T)
        return theo_points, - invert_teta

    def get_roi(self, i, points, teta, size = (10,4)):

        nrows=size[0]
        ncols=size[1]
        p0 = i + i/(nrows-1)
        points_idx = [p0, p0+1, p0+nrows, p0+nrows+1]
        np_points = [points[p].astype(np.int32) for p in points_idx]

        pts = np.array([(p[0], p[1]) for p in np_points])

        a,b,c,d = pts[:,0] +  1j * pts[:,1]
        size = (1 + int(round(abs(d-b))), 1 + int(round(abs(a-b))))

        x,y,w,h =  cv2.boundingRect(pts.reshape(4,1,2))
        box_a,box_b,box_c,box_d = y, y+h, x, x+w


        rotat_mat = self.make_rotation_mat(teta)
        rotat_mat = np.column_stack([rotat_mat, [ x - pts[0,0], y - pts[0,1]]])

        return (box_a,box_b,box_c,box_d), rotat_mat,  size