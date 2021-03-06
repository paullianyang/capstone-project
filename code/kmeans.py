'''
KMeans allowing custom distance functions.
Used for driving distance

Come back to this: Perhaps calculate a distance matrix
and then fetch the distance from the matrix
'''
from __future__ import division
import random
import numpy as np
from scipy.spatial.distance import euclidean, cityblock
import utils


def driving_distance(from_coord, to_coord, gmaps=True):
    '''
    INPUT: lat/long tuple identifying origin,
           lat/long tuple identifying destination
    OUTPUT: distance in meters
    '''
    from_lat, from_long = from_coord
    to_lat, to_long = to_coord
    return utils.OSRM(from_lat, from_long, to_lat, to_long, gmaps=gmaps).distance()


class kmeans(object):
    def __init__(self, k, init='k++', max_iter=-1,
                 verbose=False, distance='euclidean'):
        '''
        k: number of clusters
        init: choose initial metrics randomly or method of kmeans++
        max_iter: set a maximum number of iterations for convergence.
                  The default is -1, which sets no max
        verbose: if True, prints the iteration number and
                 the current centers for each iteration
        distance: sets the distance metric to minimize for
        random_state: sets a random seed
        '''
        distance_methods = {'euclidean': euclidean,
                            'cityblock': cityblock,
                            'driving': driving_distance}

        self.k = k
        self.init = init
        self.max_iter = max_iter
        self.verbose = verbose
        self.cluster_centers_ = None
        self.labels_ = None
        self.distance = distance_methods[distance]

    def fit(self, X):
        '''
        INPUT: numpy 1-D matrix
        OUTPUT: none
        '''
        if self.init == 'k++':
            self.kplusplus_init(X)
        else:
            self.cluster_centers_ = np.array(random.sample(X, self.k))
        counter = 0
        while True:
            if self.max_iter > 0 or self.verbose:
                if counter == self.max_iter:
                    break
                else:
                    counter += 1
            labels = self.predict(X)

            new_centers = np.zeros(self.cluster_centers_.shape)
            for i in np.arange(self.k):
                new_centers[i] = np.mean(X[labels == i], axis=0)
            if (new_centers == self.cluster_centers_).all():
                break
            self.cluster_centers_ = new_centers
            if self.verbose:
                print 'iter: ', counter
                print new_centers
        self.labels_ = labels

    def predict(self, X, gmaps=True):
        '''
        INPUT: 1-D numpy array, T/F to allow gmaps API
        OUTPUT: 1-D numpy array

        returns the closest center for each point
        '''
        labels = np.zeros(X.shape[0])
        for i, datapoint in enumerate(X):
            distances = [self.distance(datapoint, center, gmaps)
                         for center in self.cluster_centers_]
            # OSRM doesn't have driving directions for all points
            # usually I back into the gmaps API
            # but the simulation easily goes over the request limit
            # For the simulation, if 'Failed', we'll choose a new point
            if 'Failed' in distances:
                return 'Failed'
            labels[i] = np.argmin(distances)
            if self.verbose:
                if i % 100 == 0:
                    print '%.2f%%' % (i/X.shape[0]*100)
        return labels

    def kplusplus_init(self, X):
        '''
        INPUT: 1-D numpy array
        OUTPUT: None

        picks initial cluster centers weighted against
        how close they are from another
        '''
        self.cluster_centers_ = np.array(random.sample(X, 1))
        while self.cluster_centers_.shape[0] < self.k:
            distances = np.array([min([self.distance(datapoint, center)
                                 for center in self.cluster_centers_])
                                 for datapoint in X])
            probs = distances/distances.sum()
            cumprobs = probs.cumsum()
            i = np.where(cumprobs >= random.random())[0][0]
            self.cluster_centers_ = np.row_stack((self.cluster_centers_, X[i]))
            if self.verbose:
                print self.cluster_centers_
