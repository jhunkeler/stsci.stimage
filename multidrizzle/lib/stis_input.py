#
#   Authors: Christopher Hanley
#   Program: stis_input.py
#   Purpose: Class used to model STIS specific instrument data.

from pytools import fileutil
import numpy as N

from input_image import InputImage
from imagemanip import interp2d

class STISInputImage (InputImage):

    SEPARATOR = '_'

    def __init__(self, input,dqname,platescale,memmap=0):
        InputImage.__init__(self,input,dqname,platescale,memmap=0)
        
        # define the cosmic ray bits value to use in the dq array
        self.cr_bits_value = 8192
        self.platescale = platescale
        self._effGain = 1
                
    def getflat(self):
        """

        Purpose
        =======
        Method for retrieving a detector's flat field.  For STIS there are three 
        
        
        This method will return an array the same shape as the
        image.
        
        :units: electrons

        """

        # The keyword for STIS flat fields in the primary header of the flt
        
        lflatfile = self.header['LFLTFILE']
        pflatfile = self.header['PFLTFILE']
        
        # Try to open the file in the location specified by LFLTFILE.
        try:
            handle = fileutil.openImage(lflatfile,mode='readonly',memmap=0)
            hdu = fileutil.getExtn(handle,extn=self.extn)
            lfltdata = hdu.data
            if lfltdata.shape != self.image_shape:
                lfltdata = interp2d.expand2d(lfltdata,self.image_shape)
        except:
            # If the user forgot to specifiy oref try looking for the reference
            # file in the current directory
            try:
                handle = fileutil.openImage(lfltfile[5:],mode='readonly',memmap=0)
                hdu = fileutil.getExtn(handle,extn=self.extn)
                lfltdata = hdu.data
            # No flat field was found.  Assume the flat field is a constant value of 1.
            except:
                lfltdata = n.ones(self.image_shape,dtype=self.image_dtype)
                str = "Cannot find file "+filename+".  Treating flatfield constant value of '1'.\n"
                print str
        
        # Try to open the file in the location specified by PFLTFILE.
        try:
            handle = fileutil.openImage(pflatfile,mode='readonly',memmap=0)
            hdu = fileutil.getExtn(handle,extn=self.extn)
            pfltdata = hdu.data
        except:
            # If the user forgot to specifiy oref try looking for the reference
            # file in the current directory
            try:
                handle = fileutil.openImage(pfltfile[5:],mode='readonly',memmap=0)
                hdu = fileutil.getExtn(handle,extn=self.extn)
                pfltdata = hdu.data
            # No flat field was found.  Assume the flat field is a constant value of 1.
            except:
                pfltdata = n.ones(self.image_shape,dtype=self.image_dtype)
                str = "Cannot find file "+filename+".  Treating flatfield constant value of '1'.\n"
                print str
        
        print "lfltdata shape: ",lfltdata.shape
        print "pfltdata shape: ",pfltdata.shape
        flat = lfltdata * pfltdata
        
        return flat

    def setInstrumentParameters(self, instrpars, pri_header):
        """ This method overrides the superclass to set default values into
            the parameter dictionary, in case empty entries are provided.
        """
        if self._isNotValid (instrpars['gain'], instrpars['gnkeyword']):
            instrpars['gnkeyword'] = 'ATODGAIN'
        if self._isNotValid (instrpars['rdnoise'], instrpars['rnkeyword']):
            instrpars['rnkeyword'] = 'READNSE'
        if self._isNotValid (instrpars['exptime'], instrpars['expkeyword']):
            instrpars['expkeyword'] = 'EXPTIME'
        if instrpars['crbit'] == None:
            instrpars['crbit'] = self.cr_bits_value

        self._gain      = self.getInstrParameter(instrpars['gain'], pri_header,
                                                 instrpars['gnkeyword'])
        self._rdnoise   = self.getInstrParameter(instrpars['rdnoise'], pri_header,
                                                 instrpars['rnkeyword'])
        self._exptime   = self.getInstrParameter(instrpars['exptime'], pri_header,
                                                 instrpars['expkeyword'])
        self._crbit     = instrpars['crbit']

        if self._gain == None or self._rdnoise == None or self._exptime == None:
            print 'ERROR: invalid instrument task parameter'
            raise ValueError

    def _setMAMAchippars(self):
        self._setMAMADefaultGain()
        self._setMAMADefaultReadnoise()
     
    def _setMAMADefaultGain(self):
        self._gain = 1

    def _setMAMADefaultReadnoise(self):
        self._rdnoise = 0

class CCDInputImage(STISInputImage):

    def __init__(self, input, dqname, platescale, memmap=0):
        STISInputImage.__init__(self,input,dqname,platescale,memmap=0)
        self.instrument = 'STIS/CCD'
        self.full_shape = (1024,1024)
        self.platescale = platescale
  
        if ( self.amp == 'D' or self.amp == 'C' ) : # cte direction depends on amp 
            self.cte_dir =  1 
        if ( self.amp == 'A' or self.amp == 'B' ) :
            self.cte_dir =  -1  

    def getdarkcurrent(self):
        darkcurrent = 0.009 #electrons/sec
        return darkcurrent / self.getGain()
    
    def getReadNoise(self):
        """
        
        Purpose
        =======
        Method for trturning the readnoise of a detector (in DN).
        
        :units: DN
        
        """
        return self._rdnoise / self.getGain()

class NUVInputImage(STISInputImage):
    def __init__(self, input, dqname, platescale, memmap=0):
        STISInputImage.__init__(self,input,dqname,platescale,memmap=0)
        self.instrument = 'STIS/NUV-MAMA'
        self.full_shape = (1024,1024)
        self.platescale = platescale

        # no cte correction for STIS/NUV-MAMA so set cte_dir=0.
        print('\nWARNING: No cte correction will be made for this STIS/NUV-MAMA data.\n')
        self.cte_dir = 0  

    def setInstrumentParameters(self, instrpars, pri_header):
        """ This method overrides the superclass to set default values into
            the parameter dictionary, in case empty entries are provided.
        """
        if self._isNotValid (instrpars['gain'], instrpars['gnkeyword']):
            instrpars['gnkeyword'] = None
        if self._isNotValid (instrpars['rdnoise'], instrpars['rnkeyword']):
            instrpars['rnkeyword'] = None
        if self._isNotValid (instrpars['exptime'], instrpars['expkeyword']):
            instrpars['expkeyword'] = 'EXPTIME'
        if instrpars['crbit'] == None:
            instrpars['crbit'] = self.cr_bits_value

        self._exptime   = self.getInstrParameter(instrpars['exptime'], pri_header,
                                                 instrpars['expkeyword'])
        self._crbit     = instrpars['crbit']

        if self._exptime == None:
            print 'ERROR: invalid instrument task parameter'
            raise ValueError

        # We need to treat Read Noise and Gain as a special case since it is 
        # not populated in the STIS primary header for the MAMAs
        if (instrpars['rnkeyword'] != None):
            self._rdnoise   = self.getInstrParameter(instrpars['rdnoise'], pri_header,
                                                     instrpars['rnkeyword'])                                                 
        else:
            self._rdnoise = None
 
        if (instrpars['gnkeyword'] != None):
            self._gain = self.getInstrParameter(instrpars['gain'], pri_header,
                                                     instrpars['gnkeyword'])
        else:
            self._gain = None
 
        # We need to determine if the user has used the default readnoise/gain value
        # since if not, they will need to supply a gain/readnoise value as well                
        usingDefaultGain = False
        usingDefaultReadnoise = False
        if (instrpars['gnkeyword'] == None):
            usingDefaultGain = True
        if (instrpars['rnkeyword'] == None):
            usingDefaultReadnoise = True

        # Set the default readnoise or gain values based upon the amount of user input given.
        
        # Case 1: User supplied no gain or readnoise information
        if usingDefaultReadnoise and usingDefaultGain:
            # Set the default gain and readnoise values
            self._setMAMAchippars()
        # Case 2: The user has supplied a value for gain
        elif usingDefaultReadnoise and not usingDefaultGain:
            # Set the default readnoise value
            self._setMAMADefaultReadnoise()
        # Case 3: The user has supplied a value for readnoise 
        elif not usingDefaultReadnoise and usingDefaultGain:
            # Set the default gain value
            self._setMAMADefaultGain()
        else:
            # In this case, the user has specified both a gain and readnoise values.  Just use them as is.
            pass

    def getdarkcurrent(self):
        darkcurrent = 0.0013 #electrons/sec
        return darkcurrent / self.getGain()

class FUVInputImage(STISInputImage):
    def __init__(self, input, dqname, platescale, memmap=0):
        STISInputImage.__init__(self,input,dqname,platescale,memmap=0)
        self.instrument = 'STIS/FUV-MAMA'
        self.full_shape = (1024,1024)
        self.platescale = platescale

        # no cte correction for STIS/FUV-MAMA so set cte_dir=0.
        print('\nWARNING: No cte correction will be made for this STIS/FUV-MAMA data.\n')
        self.cte_dir = 0  

    def setInstrumentParameters(self, instrpars, pri_header):
        """ This method overrides the superclass to set default values into
            the parameter dictionary, in case empty entries are provided.
        """
        if self._isNotValid (instrpars['gain'], instrpars['gnkeyword']):
            instrpars['gnkeyword'] = None
        if self._isNotValid (instrpars['rdnoise'], instrpars['rnkeyword']):
            instrpars['rnkeyword'] = None
        if self._isNotValid (instrpars['exptime'], instrpars['expkeyword']):
            instrpars['expkeyword'] = 'EXPTIME'
        if instrpars['crbit'] == None:
            instrpars['crbit'] = self.cr_bits_value

        self._exptime   = self.getInstrParameter(instrpars['exptime'], pri_header,
                                                 instrpars['expkeyword'])
        self._crbit     = instrpars['crbit']

        if self._exptime == None:
            print 'ERROR: invalid instrument task parameter'
            raise ValueError

        # We need to treat Read Noise and Gain as a special case since it is 
        # not populated in the STIS primary header for the MAMAs
        if (instrpars['rnkeyword'] != None):
            self._rdnoise   = self.getInstrParameter(instrpars['rdnoise'], pri_header,
                                                     instrpars['rnkeyword'])                                                 
        else:
            self._rdnoise = None
        if (instrpars['gnkeyword'] != None):
            self._gain = self.getInstrParameter(instrpars['gain'], pri_header,
                                                     instrpars['gnkeyword'])
        else:
            self._gain = None
 

        if self._exptime == None:
            print 'ERROR: invalid instrument task parameter'
            raise ValueError

        # We need to determine if the user has used the default readnoise/gain value
        # since if not, they will need to supply a gain/readnoise value as well                
        usingDefaultGain = False
        usingDefaultReadnoise = False
        if (instrpars['gnkeyword'] == None):
            usingDefaultGain = True
        if (instrpars['rnkeyword'] == None):
            usingDefaultReadnoise = True

        # Set the default readnoise or gain values based upon the amount of user input given.
        
        # Case 1: User supplied no gain or readnoise information
        if usingDefaultReadnoise and usingDefaultGain:
            # Set the default gain and readnoise values
            self._setMAMAchippars()
        # Case 2: The user has supplied a value for gain
        elif usingDefaultReadnoise and not usingDefaultGain:
            # Set the default readnoise value
            self._setMAMADefaultReadnoise()
        # Case 3: The user has supplied a value for readnoise 
        elif not usingDefaultReadnoise and usingDefaultGain:
            # Set the default gain value
            self._setMAMADefaultGain()
        else:
            # In this case, the user has specified both a gain and readnoise values.  Just use them as is.
            pass
    def getdarkcurrent(self):
        darkcurrent = 0.07 #electrons/sec
        return darkcurrent / self.getGain()
