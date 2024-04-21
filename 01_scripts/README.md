## Python functions

`def multi_channel_conversion(files_path, metadata_path, files_output)`

(**file_path**: Path were the images are stored (str))
(**metadata_path**: Path were the metadata.json create with IFC is stored (str)
(**files_output**: folder were to store the multichannel images (will be created) (str)))

**Description:** Create a multichannel image from single FC images extracted with IFC. Additionally,
it adds metadatal to the .tiff header with info about the channels acquisition.


`def associate_mask(conn, dts, pth, channels)`

(**conn**: existing connection with OMERO established trough BlitzGateway;
**dts**: Dataset ID on OMERO (int);**pth**: Path were the masks are stored (str);
**channels**: number of channels for each image)

**Description:** Associate the masks annotated extracted from a .cif file using the package
IFC in OMERO. 