import numpy as np
import scipy.signal as signal
from scipy.misc import central_diff_weights

from functools import reduce, partial
from operator import mul

from itertools import repeat

from pyop import LinearOperator, matvectorized

import six

def __flip(a):
    ''' Flips all the dimensions of an array '''

    every = slice(None, None)
    reverse = slice(None, None, -1)
    for d in six.moves.range(a.ndim):
        a = a[tuple(repeat(every, d)) + (reverse,)]

    return a


def convolve(kernel, shape, order='C'):
    ''' Convolve two N-dimensional arrays as a LinearOperator.

    Note that this only implements the "same" convolution mode seen in other
    functions. This is often the desired mode for linear systems since the
    problem does not alter dimensions when the convolution is applied.

    For this operator to work, the number of dimensions in the kernel must
    match the number of fields in the shape tuple.

    Parameters
    ----------
    kernel : ndarray
        The kernel by which to do the convolving.

    shape : tuple
        The shape of the array in non-vector form.

    order = {'C', 'F', 'A'}, optional
        The order by which the vectorized array is reshaped. This is the
        same parameter as given to functions like numpy.reshape. For a
        discussion of the memory efficiency of different orders and how that
        is determined by the underlying format, see the documentation of
        commands that take an order argument.

    Returns
    -------
    LinearOperator
        A LinearOperator implementing the convolution on vectorized inputs.

    Raises
    ------
    ValueError
        When the inputs are not the same dimension.

    See Also
    --------
    scipy.signal.convolve : The array based version of this operation.
    :func:`.fft` : LinearOperator version of fftn.
    :func:`.ifft` : LinearOperator version of ifftn.

    Examples
    --------
    >>> import numpy as np
    >>> from pyop.operators import convolve
    >>> A = np.linspace(1,9,9).reshape(3,3)
    >>> kernel = np.array([[-1, 1]])
    >>> C = convolve(kernel, (3, 3))
    >>> C(np.ravel(A))
    array([-1., -1., -1., -4., -1., -1., -7., -1., -1.])
    >>> C(np.ravel(A)).reshape(3,3)
    array([[-1., -1., -1.],
           [-4., -1., -1.],
           [-7., -1., -1.]])
    '''
    if not kernel.ndim == len(shape):
        raise ValueError("kernel and shape must have "
                         "the same dimensions.")

    if not order in ('C', 'F', 'A'):
        raise ValueError("The order must be 'C', 'F', or 'A'")


    vector_length = reduce(mul, shape)
    op_shape = (vector_length, vector_length)

    dim = kernel.ndim

    adjoint_kernel = __flip(kernel)

    ## f_start is the number of extra vectors at the start of a dimension
    ## caused by the kernel. Then take shape number of vectors to get
    ## the same size.
    f_start = lambda d: (kernel.shape[d] - 1) // 2
    f_stop = lambda d: f_start(d) + shape[d]
    f_slice = tuple(
        slice(f_start(d), f_stop(d)) for d in six.moves.range(dim))

    ## The same idea as above, but the extra vectors appear in kernel.shape
    ## - 1 // 2 on the right side, so kernel.shape // 2 on the left.
    a_start = lambda d: adjoint_kernel.shape[d] // 2
    a_stop = lambda d: a_start(d) + shape[d]
    a_slice = tuple(
        slice(a_start(d), a_stop(d)) for d in six.moves.range(dim))

    ## Convert function taking a matrix input to one that operates on each
    ## column, where each column is already reshaped into the shape.
    mv = matvectorized(shape, order)

    def convSame(img, kernel, slc):
        return signal.convolve(img, kernel, 'full')[slc]


    ## The result is square, it preserves shape.
    return LinearOperator(op_shape,
        mv(partial(convSame, kernel = kernel, slc = f_slice)),
        mv(partial(convSame, kernel = adjoint_kernel, slc = a_slice)))


def gradient(derivative, points, shape, step=None, order='C'):
    ''' Approximate the derivative with a central difference.

    Parameters
    ----------
    derivative : int
        The order of the derivative to approximate.

    points : int
        The number of points in the central difference. Must be an odd
        integer greater than `derivative`.

    shape : tuple
        The shape of the array in non-vector form.

    step: tuple, optional
        The step sizes between adjacent values along each dimension in the
        array. Passing None defaults to step size 1.0 along all dimensions.

    order = {'C', 'F', 'A'}, optional
        The order by which the vectorized array is reshaped. This is the
        same parameter as given to functions like numpy.reshape. For a
        discussion of the memory efficiency of different orders and how that
        is determined by the underlying format, see the documentation of
        commands that take an order argument.

    Returns
    -------
    LinearOperator
        A LinearOperator implementing the central difference on vectorized
        inputs.

    Raises
    ------
    ValueError
        When the inputs are not the right dimensions.

    See Also
    --------
    convolve : The central difference is calculated using this LinearOperator.
    scipy.misc.central_diff_weights : The scipy function returning the
        required weights for calculating the central difference.

    Examples
    --------
    >>> import numpy as np
    >>> from pyop.operators import gradient
    >>> grad = gradient(1, 3, (5,6))
    >>> laplace = gradient(2, 3, (5,6), step=(0.5,2))
    >>> A = np.indices((5,6)).sum(0)**2 / 2.
    >>> grad(np.ravel(A)).reshape(5,6)
    array([[  0.5 ,   2.  ,   4.25,   7.  ,  10.25,   5.  ],
           [  2.  ,   4.  ,   6.  ,   8.  ,  10.  ,  -0.25],
           [  4.25,   6.  ,   8.  ,  10.  ,  12.  ,  -2.  ],
           [  7.  ,   8.  ,  10.  ,  12.  ,  14.  ,  -4.25],
           [  4.  ,   1.  ,  -0.25,  -2.  ,  -4.25, -32.  ]])
    >>> laplace(np.ravel(A)).reshape(5,6)
    array([[   2.125,    4.25 ,    2.25 ,   -3.75 ,  -13.75 ,  -32.25 ],
           [   4.25 ,    4.25 ,    4.25 ,    4.25 ,    4.25 ,   -1.875],
           [   4.125,    4.25 ,    4.25 ,    4.25 ,    4.25 ,   -3.75 ],
           [   3.75 ,    4.25 ,    4.25 ,    4.25 ,    4.25 ,   -5.875],
           [ -46.875,  -67.75 ,  -93.75 , -123.75 , -157.75 , -208.25 ]])
    '''
    # it stops being useful at all at this point
    if any(s < points for s in shape):
        raise ValueError("Shape's dims must have at least as many "
                         "points as central difference weights.")

    if step is None:
        step = (1.0, ) * len(shape)
    elif len(step) != len(shape):
        raise ValueError("Shape and step must have same ndims (length).")

    step = enumerate(float(s) ** derivative for s in step)

    # reverses the order of the weights to compensate for convolution's
    # "flipped" shift
    weights = central_diff_weights(points, derivative)[::-1]

    # create a kernel with ndim specified by shape, each of length points
    kernel = np.zeros((points, ) * len(shape))
    # slice that gets the center values along first dimension
    slc = (slice(None), ) + (points // 2, ) * (kernel.ndim - 1)

    # fill in kernel along the center of each dimension
    for dim, s in step:
        kernel[slc[-dim:] + slc[:-dim]] += weights / s

    return convolve(kernel, shape, order)
