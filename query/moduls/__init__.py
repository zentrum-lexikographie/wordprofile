import warnings


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""

    def fn(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        res = func(*args, **kwargs)
        print("-- Call to deprecated function {} with \n  Args: ({},{})\n  Return: {}".format(
            func.__name__,
            args,
            kwargs,
            res
        ))
        return res

    fn.__name__ = func.__name__
    fn.__doc__ = func.__doc__
    fn.__dict__.update(func.__dict__)
    return fn
