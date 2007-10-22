#  Program: parseIVM.py
#  Author:  Christopher Hanley
#  History:
#   Version 0.1, 12/06/2004: Initial Creation -- CJH
#   Version 0.2, 01/21/2005: Completely reworked logic for parsing the input lines
#       for supporting the parseinput function in the pytools module.  -- CJH

__version__ = '0.2 (01/21/2005)'
__author__  = 'Christopher Hanley'

import pydrizzle
from pydrizzle import buildasn
from pytools import fileutil

import glob
from glob import glob

def parseIVM(inputlist):
    """
    FUNCTION: parseIVM
    PURPOSE : the parseIVM function is used to take the Python list generated by
              the parseinput function and split each entry on white space.  If there
              is more then one entry per line, we assume that the second entry is the
              name of an inverse variance map (IVM) file.  We separate the 
              entries into two lists, one for the input file names and a second for
              the IVM files.  We also make certain that if IVM files are provided, that
              there is one file for each input.  If not, a runtime exception is raised.
    INPUT   : inputlist - string object
    OUTPUT  : newinputlist - python list containing names of input files to be processed
              ivmlist - python list containg names of ivm files to be processed.              
    """

    # Define local variables
    newinputlist = []
    ivmlist = []

    for line in inputlist:
        entry = line.split()
        if ( len(entry) != 2):
            errorstr =  "#######################################\n"
            errorstr += "#                                     #\n"
            errorstr += "# ERROR:                              #\n"
            errorstr += "#  There number of science inputs     #\n"
            errorstr += "#  does not equal the number of IVM   #\n"
            errorstr += "#  file inputs.  An IVM file must be  #\n"
            errorstr += "#  provided for every science input   #\n"
            errorstr += "#  file.  Please see the HELP file    #\n"
            errorstr += "#  for more information.              #\n"
            errorstr += "#                                     #\n"
            errorstr =  "#######################################\n"
            raise ValueError, errorstr
        
        newinputlist.append(entry[0].strip())
        ivmlist.append(entry[1].strip())

    # Use the glob function to ensure that the files are on disk and
    # not wildcards
    for file in ivmlist:
        namelist = glob(file)
        if (len(namelist) != 1):
            errorstr =  "#######################################\n"
            errorstr += "#                                     #\n"
            errorstr += "# IVM FILE INPUT ERROR:               #\n"
            errorstr += "#  The following file cannot be found #\n"
            errorstr += "#  on disk:                           #\n"
            errorstr += "         "+str(file)+'\n'
            errorstr += "#                                     #\n"
            errorstr += "#######################################\n"
            raise ValueError, errorstr

    for file in newinputlist:
        namelist = glob(file)
        if (len(namelist) != 1):
            errorstr =  "#######################################\n"
            errorstr += "#                                     #\n"
            errorstr += "# INPUT FILE INPUT ERROR:             #\n"
            errorstr += "#  The following file cannot be found #\n"
            errorstr += "#  on disk:                           #\n"
            errorstr += "         "+str(file)+'\n'
            errorstr += "#                                     #\n"
            errorstr += "#######################################\n"
            raise ValueError, errorstr
    
    message = "\nProcessing IVM files: " + str(len(newinputlist)) + " Science Images, " \
        + str(len(ivmlist)) + " IVM files\n" 
    print message
    
    return newinputlist,ivmlist
    
