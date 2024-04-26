import os
import uuid
import json

import omero_rois
import tifffile
import numpy as np
import omero

from tifffile import TiffFile
from skimage.io import imread
from skimage.filters import threshold_otsu
from omero.gateway import BlitzGateway
from ome_types import to_xml, OME
from ome_types.model import Image, Pixels, Channel, TiffData


def multi_channel_conversion(files_path, metadata_path, files_output):
    with open(metadata_path, 'r') as file:
        metadata = json.load(file)
    channels = metadata['wavelenght']
    channels = [item for sublist in channels for item in sublist]
    print(channels)
    os.chdir(files_path)
    files = sorted(os.listdir(files_path), key=str.lower)
    try:
        len(files) % len(channels) != 0
    except NameError:
        print(f"Something wrong with the file number, not multiples of {len(channels)}")
    else:
        os.mkdir(files_output)
        block_size = len(channels)
        array_list = []
        round = 0
        for i in range(0, len(files), block_size):
            block_files = files[i:i + block_size]
            array_list.clear()
            for im in block_files:
                img = tifffile.imread(im)
                array = np.rint((np.asarray(img) / 256) * 65535).astype(np.uint16)
                array_list.append(array)
                with TiffFile(f'{im}') as tif:
                    sample = tif.pages[0]
                    dtype = sample.dtype
                    pixel = tif.pages[0].tags["SamplesPerPixel"].value
                    width = tif.pages[0].tags["ImageWidth"].value
                    lenght = tif.pages[0].tags["ImageLength"].value
                    bits = tif.pages[0].tags["BitsPerSample"].value
            xml_channel_list = []
            stacked_array = np.stack(array_list, axis=2)
            transposed_array = np.transpose(stacked_array, (2, 0, 1))
            file_name = block_files[0]
            file_name = file_name[:-10]
            for count, value in enumerate(channels):
                if value == 0:
                    chn = Channel(
                        id=f"Channel:{round}:{count}",
                        acquisition_mode="BrightField",
                        samples_per_pixel = f"{pixel}"
                    )
                    xml_channel_list.append(chn)
                else:
                    chn = Channel(
                        id=f"Channel:{round}:{count}",
                        acquisition_mode="FluorescenceCorrelationSpectroscopy",
                        fluor="Natural",
                        excitation_wavelength= int(value),
                        excitation_wavelength_unit="nm"
                    )
                    xml_channel_list.append(chn)
            ome = OME(
                uuid="urn:uuid:" + str(uuid.uuid4()),
                creator="tifffile --v tifffile 2023.7.10")
            tfd = TiffData(
                first_c=0,
                first_t=0,
                first_z=0,
                ifd=0,
                plane_count=1,
                uuid=TiffData.UUID(
                    file_name=f"{file_name}.tiff",
                    value="urn:uuid:" + str(uuid.uuid4())
                ))
            img = Image(
                id=f"Image:{round}",
                name=f"{file_name}.tiff",
                pixels=Pixels(
                    id=f"Pixels:{round}",
                    channels=xml_channel_list,
                    tiff_data_blocks=[tfd],
                    type=f"{dtype}",
                    dimension_order="XYCTZ",
                    significant_bits = f"{bits}",
                    size_x=f"{width}",
                    size_y=f"{lenght}",
                    size_z=1,
                    size_c= f"{len(channels)}",
                    size_t=1)
            )
            ome.images.append(img)
            ome = to_xml(ome, validate=True)
            tifffile.imwrite(f"{files_output}/{file_name}.ome.tiff",
                             transposed_array,
                             dtype=transposed_array.dtype,
                             shape=transposed_array.shape,
                             metadata={'axes': 'CYX'},
                             description= ome)
            round += 1


def associate_mask(user, passw, dts, path):
    conn = BlitzGateway(user, passw, host="localhost", port=4064, secure=True)
    if conn.connect() is False:
        print("Not connected to OMERO instance. Please retry")
    else:
        print("Connection established. Starting Importing Mask!")
        def create_roi(img, shapes):
            roi = omero.model.RoiI()
            roi.setImage(img._obj)
            for shape in shapes:
                roi.addShape(shape)
            updateService.saveObject(roi)
        dts = str(dts.replace("Dataset:", ""))
        dataset = conn.getObject("Dataset", dts)
        ID = []
        for image in dataset.listChildren():
            ID.append(image.getId())
        os.chdir(path)
        files = sorted(os.listdir(path), key=str.lower)
        for im in ID:
            updateService = conn.getUpdateService()
            print(f"Processing Image with ID:{im}")
            image = conn.getObject("Image", im)
            channel = 0
            for i in files:
                if channel <= 11:
                    img = imread(i)
                    thresh = threshold_otsu(img)
                    binary = img > thresh
                    mask = omero_rois.mask_from_binary_image(binary, rgba=(255, 0, 0, 150), z=0, c=channel, t=0,
                                                             text=f"Channel_{channel}", raise_on_no_mask=False)
                    create_roi(image, [mask])
                    channel += 1
                    os.remove(i)
                else:
                    files = files[12:]
                    print(f"Finish mask upload with ID:{im}")
                    break
        conn.close()
