__author__ = 'quentin'

import itertools
import cv2
import cv
import numpy as np



class ROISplitter(object):
    def __init__(self, image, grid_size=(10,4)):
        corners = self.show_corners(image)
        decimated = self.decimate(corners)
        theo_points, teta = self.find_grid(decimated)
        all_rois = self.make_all_rois(theo_points, teta, grid_size)
        self.all_rois = self.filter_rois(all_rois)
        np.random.seed(0)

    @property
    def nrois(self):
        return len(self.all_rois)

    def make_all_rois(self, theo_points, teta, grid_size):
        nrows = (grid_size[0] - 1)
        ncols = (grid_size[1] - 1)
        n_rois = nrows *  ncols

        all_rois = [self.get_roi(r, theo_points, teta) for r in range(n_rois)]

        order = np.arange(n_rois).reshape((ncols, nrows)).T.flatten()
        print order
        return [all_rois[i] for i in order]




    def filter_rois(self, all_rois, min_ar=3):
        out = [(t,m,size) for t,m,size in all_rois if size[0] /float(size[1]) > min_ar]
        return out


    def split(self, image, which):
        (box_a,box_b,box_c,box_d), rotat_mat,  size = self.all_rois[which]
        roi_rec = image[box_a:box_b, box_c:box_d]
        roi = cv2.warpAffine(roi_rec, rotat_mat, size, flags=cv2.INTER_CUBIC);
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

    def distance_fun(self, pts, size=(10,4)):
        nrows=size[0]
        ncols=size[1]
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        compact_c, _ ,centres_c = cv2.kmeans(pts[:,0],ncols, criteria , 5, flags=cv2.KMEANS_PP_CENTERS)
        compact_r, _ ,centres_r = cv2.kmeans(pts[:,1],nrows, criteria , 5, flags=cv2.KMEANS_PP_CENTERS)
        return np.log10(compact_c) + np.log10(compact_r), centres_c.flatten(), centres_r.flatten()

    def make_rotation_mat(self, teta):
        return np.array([
                [np.cos(teta), -np.sin(teta)],
                [np.sin(teta), np.cos(teta)],
            ])


    def find_grid(self, image, size=(10,4), teta_resolution= .01):
        points = [(j,i) for (i,j), value in np.ndenumerate(image) if value]
        best_dist = np.Inf
        for teta in np.arange(-np.pi/4, np.pi/4, teta_resolution * np.pi):
            rotat_mat = self.make_rotation_mat(teta)
            rotated_points = np.dot(points, rotat_mat.T).astype(np.float32)
            dist, centres_c, centres_r = self.distance_fun(rotated_points)
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

#
# class ROISplitter_orig(object):
#     def __init__(self, image):
#         self.h_morph_line = np.array([[0,0,0], [1,1,1], [0,0,0]],dtype=np.uint8)
#         self.v_morph_line = np.array([[0,1,0], [0,1,0], [0,1,0]],dtype=np.uint8)
#         self._rois = self.make_rois(image)
#         self._rois = self.sort_rois(self._rois)
#         #TODO align rois ?
#     @property
#     def nrois(self):
#         return len(self._rois)
#
#
#     def split(self, image,  which):
#         if which >= len(self._rois):
#             raise Exception("There are only %i ROIs" % len(self._rois))
#         a,b,c,d= self._rois[which]
#         return image[a:b, c:d]
#
#     def sort_rois(self, rois):
#         x_centers = np.array([float(c+d)/2.0 for a,b,c,d in  rois])
#         x_mean = np.mean(x_centers)
#         left_rois = np.array([ r for r, xc in  zip(rois,x_centers) if xc < x_mean])
#         right_rois = np.array([ r for r, xc in  zip(rois,x_centers) if xc >= x_mean])
#         def compare(roi1, roi2):
#             y_center1 = float(roi1[0] + roi1[1])/2.0
#             y_center2 = float(roi2[0] + roi2[1])/2.0
#             return int(y_center1 - y_center2)
#         left_rois = sorted(left_rois, cmp=compare)
#         right_rois = sorted(right_rois, cmp=compare)
#         sorted_rois = [item for sublist in zip(left_rois, right_rois) for item in sublist]
#         return sorted_rois
#
#     def filter_good_contours(self, contour, min_length=200, max_length=500, min_ar = 3.5, max_ar = 6, max_angle=20):
#         rect = cv2.minAreaRect(contour)
#         box = cv.BoxPoints(rect)
#         a = np.complex(box[0][0], box[0][1])
#         b = np.complex(box[1][0], box[1][1])
#         c = np.complex(box[2][0], box[2][1])
#         diag = np.abs(a-c)
#         aspect_ratio = np.abs(a-b)/ np.abs(c-b)
#         if aspect_ratio < 1:
#             aspect_ratio = 1/aspect_ratio
#
#
#         if diag  > max_length or diag < min_length:
#             return False
#
#         if aspect_ratio > max_ar or aspect_ratio < min_ar:
#             return False
#         if abs(rect[2] % 90) > max_angle and abs(rect[2]) > max_angle:
#             return False
#         return True
#     def make_rois(self, image, expected_number=18):
#         """
#         Find ROIs in the preprocessed image
#         :param image: greyscale image(CV_U8C1)
#         :return: a list of contours (1 per ROI)
#         """
#
#         # we try different thresholds to get all the contours
#         for threshold_value in reversed(range(0, 101,5)):
#             preprocessed_mat = self.pre_process(image)
#             _ , bin_mat = cv2.threshold(preprocessed_mat, threshold_value, 255,cv.CV_THRESH_BINARY_INV)
#             contours, hiera = cv2.findContours(bin_mat, cv.CV_RETR_CCOMP,cv.CV_CHAIN_APPROX_SIMPLE)
#             if len(contours) < expected_number:
#                 continue
#             #remove holes
#             contours = [c for (c,h) in zip(contours,hiera[0]) if h[3] == -1 and len(c) >3]
#
#             contours = filter(self.filter_good_contours, contours)
#             if len(contours) == expected_number:
#                 break
#
#         if len(contours) != expected_number:
#             raise Exception("len(contours) [{0}] != expected_number [{1}]".format(len(contours), expected_number))
#
#         roi_coord = []
#         for c in contours:
#             x,y,w,h = cv2.boundingRect(c)
#             roi_coord.append((y, y+h, x, x+w))
#         return roi_coord
#
#     def pre_process(self, image, iter_first_pass=10, iter_second_pass=64):
#         """
#         Preprocessed the frame of a grid and return only the vertical and horizontal, contrasted, lines
#
#         :param image: the original image (CV_U8C1)
#         :param iter_first_pass: number of erosions/dilatations in first pass
#         :param iter_second_pass: number of erosions/dilatations in second  pass
#         :return: an image (CV_U8C1)
#         """
#
#         # vertically close
#         v_dilated_mat  = cv2.dilate(image, self.v_morph_line, iterations=iter_first_pass)
#         v_eroded_mat = cv2.erode(v_dilated_mat, self.v_morph_line, iterations=iter_first_pass)
#
#         # horizontally eroded
#         h_dilated_mat  = cv2.dilate(image, self.h_morph_line, iterations=iter_first_pass)
#         h_eroded_mat = cv2.erode(h_dilated_mat, self.h_morph_line, iterations=iter_first_pass)
#
#         sqr_dilated_mat  = cv2.dilate(image, None, iterations=10)
#
#         h_diff_img = cv2.subtract(sqr_dilated_mat, h_eroded_mat)
#         h_diff_img = cv2.erode(h_diff_img, self.h_morph_line, iterations=iter_second_pass)
#         h_diff_img = cv2.dilate(h_diff_img, self.h_morph_line, iterations=iter_second_pass)
#
#         v_diff_img = cv2.subtract(sqr_dilated_mat, v_eroded_mat)
#         v_diff_img = cv2.erode(v_diff_img, self.v_morph_line, iterations=iter_second_pass)
#         v_diff_img = cv2.dilate(v_diff_img, self.v_morph_line, iterations=iter_second_pass)
#
#         diff_img = cv2.add(v_diff_img, h_diff_img)
#         diff_img  = cv2.dilate(diff_img,None, iterations=3)
#         med_img = cv2.medianBlur(diff_img, 101)
#         diff_img = cv2.subtract(diff_img, med_img)
#         return diff_img
