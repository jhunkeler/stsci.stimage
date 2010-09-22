import os, string

__taskname__ = 'sextractorpars'


def getHelpAsString():
    """ Teal help function to describe the parameters being set
        Descriptions of parameters come from .help file
    """
    helpString = ""
    #get the local library directory where the code is stored
    localDir=os.path.split(__file__)
    helpfile=__taskname__.split(".")
    
    helpfile=localDir[0]+"/"+helpfile[0]+".help"
    
    if os.access(helpfile,os.R_OK):
        fh=open(helpfile,'r')
        fhlines=fh.readlines()
        fh.close()

        helpString+=string.join(fhlines)

    return helpString

def run(configobj=None):
    """ Sextractor parameters which can be set by `tweakreg`_.
    """
    pass

run.__doc__ += getHelpAsString()