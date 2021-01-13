# sbxreader

Python module to read Neurolabware Scanbox files.

## Usage

### Open a scanbox file

```python
from sbxreader import sbx_memmap
dat = sbx_memmap(`filename.sbx`)

# This memory maps the file, the shape is:
# NFRAMES x NPLANES x NCHANNELS x HEIGHT x WIDTH
# To access frames treat it like a numpy array
# but create a new array when getting the frame:
first20frames = np.array(dat[:20])

# access metadata as a dictionary
print(dat.metadata)

# number of invalid columns when recording in bidirectional mode
print(dat.ndeadcols)
```

### Get metadata from the file

```python
from sbxreader import sbx_get_metadata
metadata = sbx_get_metadata(`filename.sbx`)

print(metadata) # dictionary with the recording metadata
```

### Parse the mat file

```python
from sbxreader import sbx_get_info
info = sbx_get_info(`filename.sbx`)

# Returns a scipy.io matlab structure 
```

## Instalation

``pip install sbxreader``

source code is in  ``https://github.com/jcouto/sbxreader.git``