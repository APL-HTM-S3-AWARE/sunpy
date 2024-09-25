import os
import re
import glob
import pathlib
import collections
import urllib.request

HDPair = collections.namedtuple("HDPair", ["data", "header"])


def parse_uri(obj_list, f, **kwargs):
    """
    Read in a series of fsspec OpenFile objects using the function *f*

    Parameters
    ----------
    obj_list : list of fsspec.core.OpenFile objects
    f : callable
        Must return a list of read-in data.
    kwargs :
        Additional keyword arguments are handed to ``f``.

    Returns
    -------
    list
        List of files read in by ``f``.
    """
    read_files = []
    for obj in obj_list:
        fs = obj.fs
        path = obj.path
        if fs.isfile(path):
            uri = fs.unstrip_protocol(path)
            read_files += f(uri, **kwargs)
        elif fs.isdir(path):
            for afile in sorted(fs.glob(path + "/*")):
                uri = fs.unstrip_protocol(afile)
                read_files += f(uri, **kwargs)
    return read_files


def parse_path(path, f, **kwargs):
    """
    Read in a series of files at *path* using the function *f*.

    Parameters
    ----------
    path : pathlib.Path
    f : callable
        Must return a list of read-in data.
    kwargs :
        Additional keyword arguments are handed to ``f``.

    Returns
    -------
    list
        List of files read in by ``f``.
    """
    if not isinstance(path, os.PathLike):
        raise ValueError("path must be a pathlib.Path object")
    path = path.expanduser()
    if is_file(path):
        return f(path, **kwargs)
    elif is_dir(path):
        read_files = []
        for afile in sorted(path.glob("*")):
            read_files += f(afile, **kwargs)
        return read_files
    elif glob.glob(str(path)):
        read_files = []
        for afile in sorted(glob.glob(str(path))):
            afile = pathlib.Path(afile)
            read_files += f(afile, **kwargs)
        return read_files
    else:
        raise ValueError(f"Did not find any files at {path}")


# In python<3.8 paths with un-representable chars (ie. '*' on windows)
# raise an error, so make our own version that returns False instead of
# erroring. These can be removed when we support python >= 3.8
# https://docs.python.org/3/library/pathlib.html#methods
def is_file(path):
    try:
        return path.is_file()
    except Exception:
        return False


def is_dir(path):
    try:
        return path.is_dir()
    except Exception:
        return False


def possibly_a_path(obj):
    """
    Check if ``obj`` can be coerced into a pathlib.Path object.
    Does *not* check if the path exists.
    """
    try:
        pathlib.Path(obj)
        return True
    except Exception:
        return False


def is_url(obj):
    """
    Check if the given object is a valid URL.

    Parameters
    ----------
    obj : str
        The object to check.

    Returns
    -------
    bool
        True if the object is a valid URL, False otherwise.
    """
    try:
        urllib.request.urlopen(obj)
        return True
    except Exception:
        return False


def is_uri(obj):
    """
    Check if the given object is a valid URI.

    Parameters
    ----------
    obj : str
        The object to check.

    Returns
    -------
    bool
        True if the object is a valid URI, False otherwise.
    """
    try:
        _RFC3896_ = re.compile(r"^[A-Za-z][A-Za-z0-9+\-+.]*://")
        return bool(_RFC3896_.match(obj)) and not obj.startswith(("http://", "https://"))
    except Exception:
        return False


def string_is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
