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
# BUT create a new array when getting the frame:
# that is needed because the file is memory mapped.

stack = np.array(dat[:20])

# access metadata as a dictionary
print(dat.metadata)

# number of invalid columns when recording in bidirectional mode
print(dat.ndeadcols)
```

### Command line tool

The reader includes a file viewer to explore raw data.
From the command line (not the python terminal) do:

``sbxviewer <filename>``

This requires additional dependencies: ``opencv-python`` ``PyQt5`` and ``pyqtgraph``
The dependencies are installed using ``pip`` if not present.

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

Source code is in [https://github.com/jcouto/sbxreader.git](https://github.com/jcouto/sbxreader.git)

To install from source:
 1. clone the repository
 2. run the command ``python setup.py develop``