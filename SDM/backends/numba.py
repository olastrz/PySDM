"""
Created at 24.07.2019

@author: Piotr Bartman
@author: Sylwester Arabas
"""

import numpy as np
import numba


# TODO backend.storage overrides __getitem__

class Numba:
    storage = np.ndarray

    @staticmethod
    def array(shape, type):
        if type is float:
            data = np.full(shape, np.nan, dtype=np.float)
        elif type is int:
            data = np.full(shape, -1, dtype=np.int)
        else:
            raise NotImplementedError
        return data

    @staticmethod
    def from_ndarray(array):
        if array.ndim > 1:
            result = array.copy()
        else:
            result = np.reshape(array.copy(), (1, -1))
        return result

    @staticmethod
    # @numba.njit()
    def shuffle(data, length, axis):
        idx = np.random.permutation(length)
        Numba.reindex(data, idx, length, axis=axis)

    @staticmethod
    # @numba.njit()
    def reindex(data, idx, length, axis):
        if axis == 1:
            data[:, 0:length] = data[:, idx]
        else:
            raise NotImplementedError

    @staticmethod
    def argsort(idx, data, length):
        idx[0:length] = data[0:length].argsort()

    @staticmethod
    def stable_argsort(idx: np.ndarray, data: np.ndarray, length: int):
        idx[0:length] = data[0:length].argsort(kind='stable')

    @staticmethod
    def amin(data):
        result = np.amin(data)
        return result

    @staticmethod
    def amax(data):
        result = np.amax(data)
        return result

    @staticmethod
    def transform(data, func, length):
        data[:length] = np.fromfunction(
            np.vectorize(func, otypes=(data.dtype,)),
            (length,),
            dtype=np.int
        )

    @staticmethod
    def foreach(data, func):
        for i in range(len(data)):
            func(i)

    @staticmethod
    def shape(data):
        return data.shape

    @staticmethod
    def urand(data, min=0, max=1):
        data[:] = np.random.uniform(min, max, data.shape)

    # TODO do not create array
    @staticmethod
    def remove_zeros(data, idx, length) -> int:
        for i in range(length):
            if data[0][idx[0][i]] == 0:
                idx[0][i] = idx.shape[1]
        idx.sort()
        return np.count_nonzero(data)

    @staticmethod
    @numba.njit("void(int32[:], int32[:], int32, float64[:,:], float64[:])")
    def extensive_attr_coalescence(n, idx, length, data, gamma):
        # TODO in segments
        for i in range(length // 2):
            j = 2 * i
            k = j + 1

            j = idx[j]
            k = idx[k]

            if n[j] < n[k]:
                j, k = k, j
            g = min(gamma[i], n[j] // n[k])

            new_n = n[j] - g * n[k]
            if new_n > 0:
                data[:, k] += g * data[:, j]
            else:  # new_n == 0
                data[:, j] = g * data[:, j] + data[:, k]
                data[:, k] = data[:, j]

    @staticmethod
    @numba.njit("void(int32[:], int32[:], int32, float64[:])")
    def n_coalescence(n, idx, length, gamma):
        # TODO in segments
        for i in range(length // 2):
            j = 2 * i
            k = j + 1

            j = idx[j]
            k = idx[k]

            if n[j] < n[k]:
                j, k = k, j
            g = min(gamma[i], n[j] // n[k])

            new_n = n[j] - g * n[k]
            if new_n > 0:
                n[j] = new_n
            else:  # new_n == 0
                n[j] = n[k] // 2
                n[k] = n[k] - n[j]

    @staticmethod
    @numba.njit("void(float64[:], float64[:], int32[:], int64)")
    def sum_pair(data_out, data_in, idx, length):
        for i in range(length // 2):
            data_out[i] = data_in[idx[2 * i]] + data_in[idx[2 * i + 1]]

    @staticmethod
    @numba.njit("void(float64[:], int32[:], int32[:], int64)")
    def max_pair(data_out, data_in, idx, length):
        for i in range(length // 2):
            data_out[i] = max(data_in[idx[2 * i]], data_in[idx[2 * i + 1]])

    @staticmethod
    def multiply(data, multiplier):
        data *= multiplier

    @staticmethod
    def sum(data_out, data_in):
        data_out[:] = data_out + data_in

    @staticmethod
    def floor(data):
        data[:] = np.floor(data)




