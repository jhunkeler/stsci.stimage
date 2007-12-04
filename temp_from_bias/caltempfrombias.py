#! /usr/bin/env python
#
# Authors: Dave Grumm
# Program: caltempfrombias.py
# Purpose: class to process data for a given filename
# History: 10/31/07 - first version [DGrumm]
#          11/08/07 - added nonlinearity application
#          11/21/07 - minor interface changes, including reodering of input parameters
#          12/04/07 - minor interface changes: no defaults for spt_key and raw_key;
#                     under pyraf these keys are settable in both __init__() and in update_headers()

import os.path
import sys
from optparse import OptionParser
import tfbutil
import opusutil
import numpy as N
import pyfits

# Coefficients that are in the file 'temp_from_bias.define' as of 10/12/07; these need to instead
# be in a (fits) reference file.
p_c1_12=[-957.67548,0.98115373]
p_c1_13=[-2158.3193,0.96696346]
p_c1_14=[1712.0793,1.0157240]
p_c1_23=[-1211.0413,0.98569588]
p_c1_24=[2708.0526,1.0354436]
p_c1_34=[3979.5255,1.0504393]
p_c2_12=[-1673.1728,0.98142379]
p_c2_13=[2327.9074,1.0269492]
p_c2_14=[4164.0788,1.0531190]
p_c2_23=[4068.4664,1.0459572]
p_c2_24=[5923.8728,1.0715554]
p_c2_34=[1764.3628,1.0248831]
p_c3_12=[324.85806,1.0075]
p_c3_13=[492.06438,1.0050437]
p_c3_14=[835.68030,1.0096758]
p_c3_23=[215.15678,0.99948693]
p_c3_24=[539.35265,1.0032465]
p_c3_34=[327.12712,1.0039380]
c1_q1off=[0,45,75,130,180,240,315,360,420,550,510,520,450.0]
c1_q2off=[0,0,80,45,180,125,265,205,355,410,395,355,290.0]
c1_q3off=[0,10,20,25,50,62,90,95,124,164,155,155,128.0]
c1_q4off=[0,-10,35,10,70,35,125,70,145,155,167,145,105.0]
c2_q1off=[0,-5,-60,-80,-155,-185,-198]
c2_q2off=[0,-65,-115,-273,-343,-487,-500]
c2_q3off=[0,-25,-115,-180,-293,-365,-405]
c2_q4off=[0,20,-40,-5,-68,-50,-68.0]
c3_q1off=[0,0,110,110,265,240,320,320,200,340,85,225.0,90.]
c3_q2off=[0,-70,45,-105,40,-75,-5,0,-45,80,-50,105,75]
c3_q3off=[0,-55,65,-60,90,-7,68,60,0,130,-35,128,68]
c3_q4off=[0,10,125,137,300,285,375,380,255,410,105,270,100]
pt=N.zeros((3,4,2), dtype=N.float64)	# (cam, quad, [intercept, slope])
pt[0,0,:]=[145.11,0.003442]
pt[0,1,:]=[148.66098,0.0035080553]
pt[0,2,:]=[153.27612,0.0035567496]
pt[0,3,:]=[139.89991,0.0033898134]
pt[1,0,:]=[152.62181,0.0035212949]
pt[1,1,:]=[159.01768,0.0035824134]
pt[1,2,:]=[144.86,0.003425]
pt[1,3,:]=[138.44286,0.003343]
pt[2,0,:]=[147.63,0.003495]
pt[2,1,:]=[146.92948,0.0034619325]
pt[2,2,:]=[146.21557,0.0034699612]
pt[2,3,:]=[144.51,0.003455]
blind_pt_c1_1=pt[0,0,:]
blind_pt_c2_1=pt[1,0,:]
blind_pt_c3_1=pt[2,0,:]
c1_blindfac=1.49
c2_blindfac=1.00
c3_blindfac=7.40
c1_blindoff=0.793
c2_blindoff=[-0.343593]
c3_blindoff=0.476092

__version__ = "1.2"

ERROR_RETURN = 2 

class CalTempFromBias:
    """Calculate the temperature from the bias for a given filename.

    example:
       tfb = CalTempFromBias( filename, spt_key, raw_key, nref_par, force, noclean, verbosity)
       [temp, sigma, winner ]= tfb.calctemp() 
    """

    def __init__( self, input_file, spt_key=None, raw_key=None, nref_par=None,
                  force=0, noclean=False, verbosity=0):
        """constructor

        @param input_file: name of the file to be processed
        @type input_file: string
        @param spt_key: name of keyword to update in SPT file
        @type spt_key: string
        @param raw_key: name of keyword to update in RAW file
        @type raw_key: string
        @param nref_par: name of the directory containing the nonlinearity file
        @type nref_par: string
        @param force: number of algorithm whose value is to be returned,
                      regardless of which algorithm had the lowest estimated sigma.
        @type force: read as a string, but valid values are 0,1,2,3 
        @param noclean: flag to force use of UNCLEANed 0th read.
        @type noclean: string that is either True or False
        @param verbosity: verbosity level (0 for quiet, 1 verbose, 2 very verbose)
        @type verbosity: string
        """

        self.input_file = input_file
        self.spt_key = spt_key 
        self.raw_key = raw_key 
        self.nref_par = nref_par 
        self.force = force
        self.noclean = noclean
        self.verbosity = verbosity


    def calctemp(self): 
        """ Calculate the temperature from the bias for the given input file
        @return: temp, sig, winner
        @rtype: float, float, int
        """

        temp = 0.0

        spt_key = self.spt_key
        raw_key = self.raw_key 
        nref_par = self.nref_par
        noclean = self.noclean
        filename = self.input_file
        if not self.force:
           force =  '0' 
        else:
           force = str(self.force)
        verbosity = self.verbosity

        # check that specified 'force' is valid
        if (force <> None):
           if (( force <> "0") & ( force <> "1") & ( force <> "2") & ( force <> "3")):
              opusutil.PrintMsg("F","ERROR "+ str('Invalid value of ')+str(force)+ str(' specified for force'))

       # get header
        try:
           fh_raw = pyfits.open( filename ) 
        except:
           opusutil.PrintMsg("F","ERROR "+ str('Unable to open input file') + str(filename))
          
        raw_header = fh_raw[0].header

        obsmode_key = raw_header[ 'OBSMODE' ]
        obsmode = obsmode_key.lstrip().rstrip() # strip leading and trailing whitespace

        nsamp_key = raw_header[ 'NSAMP' ]
        nsamp = nsamp_key

        camera_key = raw_header[ 'CAMERA' ]
        camera = camera_key
 
        zoffdone_key = raw_header[ 'ZOFFDONE' ]
        zoffdone = zoffdone_key.lstrip().rstrip() # strip leading and trailing whitespace

        if ( obsmode <> 'MULTIACCUM'):
            opusutil.PrintMsg("F","ERROR "+ str('Image must be in MULTIACCUM mode'))

        if ( zoffdone == 'PERFORMED'):
            opusutil.PrintMsg("F","ERROR "+ str('ZOFFCORR has already been performed on this image. No temp information left'))

        # get nonlinearity file name from NLINFILE in header of input file and open it
        if nref_par is not None:  
           nref = os.path.expandvars( nref_par)
        else:
           nref = os.path.expandvars( "$nref")

        nonlinfile_key = raw_header[ 'NLINFILE' ] 
        nl_file = nonlinfile_key.split('nref$')[1]
        nonlin_file = os.path.join( nref, nl_file)

        try:
           fh_nl = pyfits.open( nonlin_file )
           self.nonlin_file = nonlin_file            
        except:
           opusutil.PrintMsg("F","ERROR "+ str('Unable to open nonlinearity file') + str(nonlin_file))

        # read data from nonlinearity file
        c1 = fh_nl[ 1 ].data; c2 = fh_nl[ 2 ].data; c3 = fh_nl[ 3 ].data

        # do some bad pixel clipping
        u = N.where((c2 > 3.6218723e-06)  | (c2 < -3.6678544e-07)) 
        uu = N.where((c2 < 3.6218723e-06) & (c2 > -3.6678544e-07))

        if len(u[0]) > 0 :
           c2[u] = N.median(c2[uu])

        u = N.where((c3 > 9.0923490e-11) | (c3 < -4.1401650e-11))
        uu = N.where((c3 < 9.0923490e-11) & (c3 > -4.1401650e-11))

        if len(u[0]) > 0:
           c3[u] = N.median(c3[uu])

        if ( nsamp <= 1 ):
           opusutil.PrintMsg("F","ERROR "+ str(' : nsamp <=1, so will not process'))
           return None, None, None

        if ( nsamp >= 3 ):       
            im0 = fh_raw[ ((nsamp-1)*5)+1 ].data  
            im1 = fh_raw[ ((nsamp-2)*5)+1 ].data
            im2 = fh_raw[ ((nsamp-3)*5)+1 ].data
            dtime0 = 0.203    # this is by definition - headers have 0.0 so can't use that
            ext_hdr1 = fh_raw[((nsamp-2)*5)+1].header
            dtime1 = ext_hdr1[ 'DELTATIM' ]
            ext_hdr2 = fh_raw[((nsamp-3)*5)+1].header
            dtime2 = ext_hdr2[ 'DELTATIM' ]

            signal_raw = (im2-im1)+(((im2-im1)/dtime2)*(dtime0+dtime1)) # total counts accumulated (1st estimate)
 
            signal0 = (signal_raw *(signal_raw*c2 + signal_raw**2*c3+1.0))/(dtime0+dtime1+dtime2) # refined 0 ADU countrate
            
            for ii in range(9):
              signal_raw = signal0*(dtime0+dtime1) # pure 1st read signal if no nonlinearity
              signal1 = (signal_raw / (signal_raw*c2 + signal_raw**2*c3 +1.0)) / (dtime0+dtime1) #1st read signal with nl
              signal_raw = (im2-im1) + (signal1*(dtime0+dtime1)) # total counts accumulated (second estimate)
              signal0 = (signal_raw * (signal_raw*c2 + signal_raw**2*c3 +1.0))/(dtime0+dtime1+dtime2) # doubly-refined 0 ADU countrate

            signal_raw = signal0 * dtime0 # pure 0th read signal if no nonlinearity 
            signal = signal_raw / (signal_raw*c2 + signal_raw**2*c3 +1.0) # 0th read total counts with nonlinearity - this is what should be subtracted from the 0th read

            clean = im0 - signal 
            if  (self.noclean == 'True'):
               clean = im0

# If there are only 2 reads, can do a partial clean. Subtraction of the signal
#   measured in this way will have a  negative 0.302s shading imprint in it. The amplitude
#   of this will be temp-dependent. Best way to deal is to decide if there is enough
#   signal to warrant a subtraction. if not, just use the 0th read without any correction.

        if ( nsamp == 2 ):       
            im0 = fh_raw[ ((nsamp-1)*5)+1 ].data
            im1 = fh_raw[ ((nsamp-2)*5)+1 ].data
            clean = im0
            signal= ((im1-im0)/0.302328 )

            if not threshold:
               threshold = 10.0  # in DN/s. Every 5 DN/s here is 5*0.203 = 1 DN in the quad median.

            if (N.median(signal*0.203) > threshold ):
               clean = im0-(signal * 0.203)
               
            if  (self.noclean == 'True'):
               clean = im0

# Following Eddie's suggestion: I'll catch these rare cases and abort by searching for:
#   nsamp=2 and filter is NOT blank, instead of original code which compares the median
#   of the signal and the threshold

            filter_key = raw_header[ 'FILTER' ] 
            filter = filter_key.lstrip().rstrip()
            filter = str('BLANK')
            if (filter <> 'BLANK'):
                opusutil.PrintMsg("F","ERROR "+ str('can not determine the temperature from the bias'))
   
# Calculate the quad medians to feed the temp algorithms; current state values are based on a border=5 mean.
        rawquads = quadmed(clean, border=5)

# This is the start of cascade to select the most optimal temp algorithm 

# ALGORITHM 1. State finding. This is the big daddy-O. ****** DISABLED FOR NOW *******
        qtemps_1 = [-1,-1,-1,-1]
        temp1 = N.mean(qtemps_1)
        sigma1 = 1e6
        state = [-1,-1,-1,-1]

#  ALGORITHM 2. Blind correction. 
        quads = rawquads
        if ( camera == 1):
            quads[0] = quads[0]+((quads[2]-poly(quads[0],p_c1_13)) * c1_blindfac)
            temp2 = poly(quads[0],blind_pt_c1_1) + c1_blindoff
            sigma2 = 1e6 	# this is an empirical quantity determined from EOL data
                            # it is used for comparison at the bottom of the cascade
        if ( camera == 2 ):
            quads[0] = quads[0]-((quads[2]-poly(quads[0],p_c2_13)) * c2_blindfac)
            temp2 = poly(quads[0],blind_pt_c2_1) + c2_blindoff
            sigma2 = 1e6 	# this is an empirical quantity determined from EOL data
                            # it is used for comparison at the bottom of the cascade
        if ( camera == 3): # this is the only one I (dmg) have tested as of 101607
           w = [4037.6680,1.1533126]
           quads[3] = (-(quads[3] - poly(quads[0],w)))
           temp2 = (quads[3]/37.0)+75.15
           sigma2 = 0.10 	# this is an empirical quantity determined from EOL data
                            # it is used for comparison at the bottom of the cascade

# ALGORITHM 3. Quietest-quad method. 
# 	       (no attempt at state removal - just use the quad(s) with smallest LVPS amplitudes)
        quads = rawquads

        if ( camera == 1 ):
           #  For NIC1, avg of quads 3 and 4 is best. RMS after avg is 38 DN (0.14 K)
           qtemps_3=[poly(quads[2],pt[camera-1,2,:]),poly(quads[3],pt[camera-1,3,:])]
           # correct from the mean to state 0
           qtemps_3 = qtemps_3 + ( N.mean([c1_q3off,c1_q4off]) / N.mean([(1./pt[camera-1,2,1]),(1./pt[camera-1,3,1])]) )
           temp3 = N.mean(qtemps_3)
           sigma3 = 0.14

        if ( camera == 2):
           # For NIC2, just quad 4 alone is best. RMS is 38 DN (0.14 K)
           qtemps_3 = poly(quads[3],pt[camera-1,3,:])
           #  correct from the mean to state 0
           qtemps_3 = qtemps_3 + ( N.mean(c2_q4off) / (1./pt[camera-1,3,1]))
           temp3 = qtemps_3
           sigma3 = 0.14

        if ( camera == 3): 
             #  For NIC3, avg of quads 2 and 3 is best. RMS after avg is 39 DN (0.14 K)
           qtemps_3 = [poly(quads[1],[153.25747,0.0037115404]),poly(quads[2],[151.03888,0.0036755942])]
           temp3 = N.mean(qtemps_3)
           sigma3 = 0.25

# Compare the error estimates of each of the algorithms and return the best one; the 
#   lowest sigma is the winner.
        winner = 1
        temp = temp1
        sig = sigma1

        if ((sigma2 < sigma1) and (sigma2 < sigma3)):
           temp = temp2
           sig = sigma2
           winner = 2
        if ((sigma3 < sigma2) and (sigma3 < sigma1)):
           temp = temp3
           sig = sigma3
           winner = 3
# This is the end of cascade to select the most optimal temp algorithm 

#  verbose output, if requested
        if (self.verbosity >1):
	    print '**************************************************************************************'
            print ' '
            print '    Camera: ',camera,'  State: ',state
            print '                                               Q1         Q2         Q3         Q4'
            print 'Temps from Algorithm 1 (state-finding)  :  ',qtemps_1[0],'  ',qtemps_1[1],'  ',qtemps_1[2],'  ',qtemps_1[3]
            print 'Temp from Algorithm 2 (blind-correction):  ',temp2
            
            if ( camera == 1):
                print 'Temp(s) from Algorithm 3 (quietest-quad):                        ',qtemps_3[0],'  ',qtemps_3[1]
            if ( camera == 2):
                print 'Temp(s) from Algorithm 3 (quietest-quad):                                   ',qtemps_3
            if ( camera == 3):
                print 'Temp(s) from Algorithm 3 (quietest-quad):             ',qtemps_3[0],'  ',qtemps_3[1]
            print '**************************************************************************************'
            print '   '
            print '     Algorithm 1: ',temp1,' (K) +/- ',sigma1,' (sigma)  ',sigma1/N.sqrt(4),' (SDOM)'
            print '     Algorithm 2: ',temp2,' (K) +/- ',sigma2,' (sigma)'
            print '     Algorithm 3: ',temp3,' (K) +/- ',sigma3,' (sigma)'
            print '     ----------------------------------------------------------'
            if (force <> None):
                print '     The algorithm selected by this routine is ',winner,'.'
            print '  '
            print '**************************************************************************************'


#  If the force keyword is set, force the output to return the value
#    from that particular algorithm, even if it wasn't the best.
        if ( force == "1"):
            print 'Forcing Algorithm 1 result to be returned, at your request...'
            winner = 1
            temp = temp1
            sig = sigma1
        if ( force == "2"):
            print 'Forcing Algorithm 2 result to be returned, at your request...'
            winner = 2
            temp = temp2
            sig = sigma2
        if ( force == "3"):
            print 'Forcing Algorithm 3 result to be returned, at your request...'
            winner = 3
            temp = temp3 
            sig = sigma3

        if (force <> '0'):
            print '... which gives temp = ' , temp,' and sigma = ' , sig

        # close any open file handles
        if fh_raw:
          fh_raw.close()
        if fh_nl:
          fh_nl.close()

        return temp, sig, winner

## end of def calctemp()

    def update_headers(self, temp, sig, winner, spt_key=None, raw_key=None, verbosity=0):  
        """ Update headers of spt_key and raw_key if requested
        @param temp: calculated temperature
        @type temp: float
        @param sig: standard deviation of calculated temperature
        @type sig: float
        @param winner: algorithm selected by script
        @type winner: int
        @param spt_key: name of keyword to update in SPT file
        @type spt_key: string
        @param raw_key: name of keyword to update in RAW file
        @type raw_key: string
        @param verbosity: verbosity level (0 for quiet, 1 verbose, 2 very verbose)
        @type verbosity: string
        @return: status (not None for failure due to key not being specified)
        @rtype: int
        """

        if (spt_key == None):   
            if (self.spt_key <> None):  # use value given in constructor
                spt_key = self.spt_key
            else:
                opusutil.PrintMsg("F","ERROR "+ str('No value has been specified for spt_key'))               
                return ERROR_RETURN
        else:
            self.spt_key = spt_key # for later use by print_pars()
            if ( verbosity > 0):
                print ' Using value of spt_key = ' , spt_key,' that has been passed to update_headers()'
    
            
        if (raw_key == None): 
            if (self.raw_key <> None):    # use value given in constructor
                raw_key = self.raw_key
            else:
                opusutil.PrintMsg("F","ERROR "+ str('No value has been specified for raw_key'))               
                return ERROR_RETURN
        else:
            self.raw_key = raw_key # for later use by print_pars()
            if ( verbosity > 0):
                print ' Using value of raw_key = ' , raw_key,' that has been passed to update_headers()'
                                
        comm = str('Temp from bias, sigma=')+str(sig)+str(' (K)')
        filename =  self.input_file

        # update spt file
        underbar = filename.find('_')
        spt_filename =  filename[:underbar] +'_spt.fits'
        fh_spt = pyfits.open( spt_filename , mode='update' )       
        spt_header = fh_spt[0].header
        spt_header.update(spt_key, temp, comment = comm)
        spt_header.update("NUMMETH", str(winner), comment = "Algorithm method used" ) 
        fh_spt.close()

        # update raw file

        fh_raw = pyfits.open( filename, mode='update' )      
        raw_header = fh_raw[0].header 
        raw_header.update(raw_key, temp, comment = comm)
        raw_header.update("NUMMETH", str(winner), comment = "Algorithm method used") 
        fh_raw.close()

        return None
        
    def print_pars(self):
        """ Print parameters used.
        """
        print ' The parameters used are :'
        print '  input_file:  ' , self.input_file
        print '  nref_par:  ' , self.nref_par
        print '  spt_key: ' ,  self.spt_key
        print '  raw_key: ' ,  self.raw_key 
        print '  force: ' ,  self.force
        print '  noclean: ' ,  self.noclean
        print '  verbosity: ' ,  self.verbosity
        print '  nonlinearity file: ' ,  self.nonlin_file   
 

#******************************************************************
# This quadmed does not have the following parameters that are in the idl version: section,
#    avg, mask, and calculates mean only ( not median ).
def quadmed( im, border):
    """  This function computes the mean in the 4 quadrants of an input NxM array

    @param im: input rectangular array
    @type im: numpy array
    @param border: border size (in pixels) aroud the perimeter of each quad to be excluded from the mean
    @type border: int
    
    """ 
#
# Following Eddie's convention, the quads are numbered as follows:
#
#    |------|-----|
#    |  Q4  |  Q3 |
#    |      |     |   as seen in the standard NICMOS/HST data format.
#    |------|-----|
#    |  Q1  |  Q2 |
#    |      |     |
#    |------|-----|
#
# optionally, you can specify a border, in pixels, around the perimeter of EACH QUAD
# to be excluded from the mean

    xsize = im.shape[1]
    ysize = im.shape[0]

    quads = N.zeros((4), dtype=N.float64)	

    if not border:
      border = 0

    x1 = 0 + border
    x2 = ((xsize/2)-1) - border
    x3 = (xsize/2) + border
    x4 = (xsize-1) - border
    y1 = 0 + border
    y2 = ((ysize/2)-1) - border
    y3 = (ysize/2) + border
    y4 = (ysize-1) - border

    quads[0] = N.mean(im[y1:y2+1,x1:x2+1])
    quads[1] = N.mean(im[y1:y2+1,x3:x4+1])
    quads[2] = N.mean(im[y3:y4+1,x3:x4+1])
    quads[3] = N.mean(im[y3:y4+1,x1:x2+1])

    return  quads


def poly( var_x, coeffs):
    """ Return linear polynomial with given coefficients.

    @param var_x: input argument
    @type var_x: scalar, vector, or array
    @param coeffs: vector of polynomial coefficients
    @type coeffs: float

    """
    poly_out = coeffs[ 0 ] + coeffs[ 1 ]* var_x
    
    return poly_out


def main( cmdline):
    """Get input file and other arguments, and call CalTempFromBias.

    The command-line options are:
        -q (quiet)
        -v (very verbose)

    @param cmdline: command-line arguments
    @type cmdline: list of strings
    """

    usage = "usage:  %prog [options] inputfile"
    parser = OptionParser( usage)

    parser.set_defaults( verbosity = tfbutil.QUIET)

    parser.add_option( "-q", "--quiet", action = "store_const",
            const = tfbutil.QUIET, dest = "verbosity",
            help = "quiet, print nothing")
    parser.add_option( "-v", "--verbose", action="store_const",
            const = tfbutil.VERY_VERBOSE, dest="verbosity",
            help="very verbose, print lots of information")

    (options, args) = parser.parse_args()
    tfbutil.setVerbosity( options.verbosity)  
    verbosity = options.verbosity

    spt_key = None 
    raw_key = None
    nref = None
    force = 0
    noclean = False

    if ( args[0] ): filename = args[0]
    if ( len(args) > 1 ): spt_key = args[1]
    if ( len(args) > 2 ): raw_key = args[2]
    if ( len(args) > 3 ): nref = args[3]
    if ( len(args) > 4 ): force = args[4]
    if ( len(args) > 5 ): noclean = args[5]

    try:
       tfb = CalTempFromBias( filename, spt_key, raw_key, nref, force, noclean, verbosity) 
       [temp, sigma, winner ]= tfb.calctemp() 

       stat = tfb.update_headers( temp, sigma, winner) 

       if ( (stat == None )and (verbosity > 0)):
            tfb.print_pars()

       del tfb

    except Exception, errmess:
       opusutil.PrintMsg("F","ERROR "+ str(errmess))

if __name__ == "__main__":

    # Process
    main( sys.argv[1:])


