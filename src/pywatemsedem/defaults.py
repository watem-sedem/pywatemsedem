ALLOWED_RASTER_FORMATS = ["idrisi", "tiff"]

PREFIX_TEMP = "pywatemsedem_"

# fix this
SUFFIXES_TIF = [".tif.aux.xml", ".tif"]
SUFFIXES_SHP = [".shp", ".cpg", ".shx", ".prj", ".dbf", ".qix"]
SUFFIXES_SAGA = [
    ".sgrd",
    ".sdat.aux.xml",
    ".mgrd",
    ".sgrid",
    ".sdat",
    ".prj",
]  # TODO: why is .prj added?
SUFFIXES_RST = [".rst", ".rdc", ".rst.aux.xml"]
SUFFIXES_TXT = [".mtab", ".txt"]

# flags used for saga_cmd
SAGA_FLAGS = "-f=q"  #: no progress report
