__version__ = '2.0'
from Convolve import *
import iraf_frame
import os
import pytools.tester


def test(*args,**kwds):
    pytools.tester.test(modname=__name__, *args, **kwds)

try:
    from svn_version import __svn_version__, __full_svn_info__
except:
    __svn_version__ = 'Unable to determine SVN revision'
    __full_svn_info__ = __svn_version__

