from scipy.io import loadmat
import os
import numpy as np

SCAN_MODE ={0:'bidirectional',
           1:'unidirectional'}
UINTMAX = np.uint16(65535)


def sbx_get_info(sbxfile):
    ''' 
    Read info from a scanbox MATLAB file 
    
    info = sbx_get_info(sbxfile)
    
    '''
    matfile = os.path.splitext(sbxfile)[0] + '.mat'
    if not os.path.exists(matfile):
        raise(OSError('Scanbox metadata file not found: {0}'.format(matfile)))
    info = loadmat(matfile,squeeze_me=True,struct_as_record=False)
    return info['info']

def sbx_get_metadata(sbxfilename):
    ''' 
    Gets metadata from a scanbox file 
    
    metadata = sbx_get_metadata(sbxfile)
    
    '''
    info = sbx_get_info(sbxfilename)
    
    if hasattr(info,'chan'): # then it is scanbox >= 3
        nchannels = info.chan.nchan
    else: # scanbox < 3
        nchannels = 1
        if info.channels == 1:
            nchannels = 2
    nplanes = 1
    etl_pos = []
    if info.volscan:
        if hasattr(info,"otwave"):
            if not isinstance(info.otwave,int):
                if len(info.otwave):
                    nplanes = len(info.otwave)
                    etl_pos = [a for a in info.otwave]
        if hasattr(info,'etl_table'):
            nplanes = len(info.etl_table)
            if nplanes > 1:
                etl_pos = [a[0] for a in info.etl_table]
            if nplanes == 0:
                nplanes = 1
    nrows,ncols = info.sz
    if os.path.exists(sbxfilename):
        max_frames = int(os.path.getsize(sbxfilename)/nrows/ncols/nchannels/2)
    else:
        print("Scanbox file {0} not found.".format(sbxfilename))
        max_frames = 0
    nframes = int(max_frames/nplanes)
    magidx = info.config.magnification - 1
    if info.scanbox_version <3:
        um_per_pixel_x = info.calibration[magidx].x
        um_per_pixel_y = info.calibration[magidx].y
    else: # this will be supported later
        um_per_pixel_x = np.nan
        um_per_pixel_y = np.nan
    
    meta = dict(scanning_mode=SCAN_MODE[info.scanmode],
                num_frames = nframes,
                num_channels = nchannels,
                num_planes = nplanes,
                frame_size = info.sz,
                num_target_frames = info.config.frames,
                num_stored_frames = max_frames,
                stage_pos = [info.config.knobby.pos.x,
                             info.config.knobby.pos.y,
                             info.config.knobby.pos.z],
                stage_angle = info.config.knobby.pos.a,
                etl_pos = etl_pos,
                filename = os.path.basename(sbxfilename),
                resonant_freq = info.resfreq,
                scanbox_version = info.scanbox_version,
                records_per_buffer = info.recordsPerBuffer,
                magnification = float(info.config.magnification_list[magidx]),
                um_per_pixel_x = um_per_pixel_x,
                um_per_pixel_y = um_per_pixel_x,
                objective = info.objective)    
    return meta

class sbx_memmap(np.memmap):
    def __new__(self,filename,sbx_metadata = None):
        '''
        Memory map a Neurolabware Scanbox file.

        data = sbx_memmap(filename)

        Data are returned as a memory mapped ndarray,
 format is NFRAMES x NPLANES x NCHANNELS x NCOLS x NROWS.

        To load the first 20 frames to memory: np.array(data[:20])
        The average of the first 20 frames np.array(np.mean(data[:20],axis=0))
        
        Use np.array() to load frames otherwise a view is returned - which is not offset corrected.
        '''
        if sbx_metadata is None:
            sbx_metadata = sbx_get_metadata(filename)
        self.metadata = sbx_metadata
        self.ndeadcols = None
        nrows,ncols = sbx_metadata['frame_size']
        sbxshape = (sbx_metadata['num_channels'],
                    ncols,nrows,
                    sbx_metadata['num_planes'],
                    sbx_metadata['num_frames'])
        self = super(sbx_memmap,self).__new__(self,filename,
                         dtype='uint16',
                         shape=sbxshape,
                         order='F')
        self = self.transpose([4,3,0,2,1])
        self.estimate_deadcols() # estimate the number of columns that are invalid in bidirectional mode because of the digitizer.
        return self
    def __getitem__(self, index):
        res = super(sbx_memmap, self).__getitem__(index)
        if type(res) is np.memmap and res._mmap is None:
            return UINTMAX - res.view(type=ndarray)
        return UINTMAX - res
    def estimate_deadcols(self):
        '''
        Estimates the number of deadcolumns if recording in binary mode.
        These happen because the digitizer is triggered in the beginning of every second line and there is some settling time.
        '''
        self.ndeadcols = 0
        if self.metadata['scanning_mode'] == 'bidirectional':
            colprofile = np.array(np.mean(self[0,0,0],axis=0))
            self.ndeadcols = np.argmin(np.diff(colprofile)) + 1 # this does not work if the PMT was completely saturated. Lets hope that never happens.
            

