# IMPORT LIBRARY
## import the library IFC and set your working directory
library(IFC)
library(jsonlite)
setwd("/working_directory_where_cif_files_are")

## get exemplary data from IFCdata - Change accordingly
test_data = system.file(package = "IFCdata", "extdata", "example.cif")
## test_data = "path_to_your_data"

#EXTRACT OFFSETS
## extracts offsets of the IFDs (Image Field Directories) within a XIF file. 
cif_offs <- getOffsets(fileName = test_data, fast = FALSE)

#EXTRACT METADATA
## get metadata: Retrieves rich information from RIF, CIF and DAF files.
metadata <- getInfo(fileName = test_data, from = "analysis")
metadata$illumination$Channel <- 1:nrow(metadata$illumination)
## extract metadata and save it as json file
wavelenght <- as.list(metadata$illumination$wavelength)
metadata_flat <- list(number_objects = metadata$objcount,
                      date = metadata$date,
                      instrument = metadata$instrument,
                      brightfield = metadata$brightfield,
                      illumination = metadata$illumination,
                      images = metadata$Images,
                      mask = metadata$masks,
                      wavelenght = wavelenght)
json_data <- toJSON(metadata_flat, pretty = TRUE)
write(json_data, file = "metadata.json")

#Extract images
## 1) count the number of objects
nobj <- as.integer(metadata$objcount)

## 2) OPTIONAL: subset objects from the .cif file
sel <- sample(0:(nobj-1), min(5, nobj))
sub_offs <- subsetOffsets(cif_offs, objects = sel, image_type = "img")

# 3) extracts IFDs (Image File Directory) in RIF or CIF files.
## IFDs contain information about images or masks of objects stored within XIF files.
## the first IFD is special in that it does not contain image of mask information but general information about the file.
IFDs <- getIFD(fileName = test_data, offsets = sub_offs)

## 4) Extract Images and Masks

objectExtract(ifd = IFDs, info = metadata, mode = "gray",
              export = "file",
              write_to = "%d/%s/%s_%o_%c.tiff",
              overwrite = TRUE,
              selection = "all",
              force_range = TRUE)


ExtractMasks_toFile(raw, objects = sel, mode = "gray", offsets = cif_offs, force_range = TRUE,
                    write_to = "%d/%s/%s_%o_%c.tiff",
                    base64_id = TRUE, add_noise = FALSE)
