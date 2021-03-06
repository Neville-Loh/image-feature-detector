from functools import wraps
from time import time

"""
Utility package to measure the time of a function.
@Author: Neville Loh
"""


def measure_elapsed_time(f):
    """
    Decorator to print the execution time of a function
    Parameters
    ----------
    f : function
        Function to be decorated
    Returns
    -------
        function wrapper
    """

    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print('[INFO] func:%-*r  Elapsed time: %2.4f sec' % (40, f.__name__, te - ts))
        return result

    return wrap
