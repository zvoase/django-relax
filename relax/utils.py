# -*- coding: utf-8 -*-


def generator_to_list(function):
    def wrapper(*args, **kwargs):
        return list(function(*args, **kwargs))
    wrapper.__name__ = function.__name__
    wrapper.__doc__ = function.__doc__
    return wrapper