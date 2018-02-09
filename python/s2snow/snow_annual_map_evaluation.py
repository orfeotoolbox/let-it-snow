#=========================================================================
#
#  Program:   lis
#  Language:  Python
#
#  Copyright (c) Germain Salgues
#  Copyright (c) Manuel Grizonnet
#
#  See lis-copyright.txt for details.
#
#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notices for more information.
#
#=========================================================================
import os
import os.path as op
import shutil
import logging
import subprocess
import multiprocessing
from lxml import etree
from xml.dom import minidom
from datetime import timedelta

from osgeo import gdal, ogr, osr
import gdalconst
from gdalconst import GA_ReadOnly

# Build gdal option to generate maks of 1 byte using otb extended filename
# syntaxx
GDAL_OPT = "?&gdal:co:NBITS=1&gdal:co:COMPRESS=DEFLATE"

# Build gdal option to generate maks of 2 bytes using otb extended filename
# syntax
GDAL_OPT_2B = "?&gdal:co:NBITS=2&gdal:co:COMPRESS=DEFLATE"

# OTB Applications
import otbApplication as otb

# Import python decorators for the different needed OTB applications
from s2snow.app_wrappers import band_math, get_app_output, super_impose, confusion_matrix

from s2snow.snow_product_parser import load_snow_product
from s2snow.utils import get_raster_as_array, apply_color_table
from s2snow.utils import str_to_datetime, datetime_to_str
from s2snow.utils import write_list_to_file, read_list_from_file
from s2snow.snow_annual_map import snow_annual_map

def get_raster_extent_as_poly(raster1):
    dataset1 = gdal.Open(raster1, gdalconst.GA_ReadOnly)
    gt1 = dataset1.GetGeoTransform()
    srs1 = osr.SpatialReference()
    srs1.ImportFromWkt(dataset1.GetProjection())
    sizeX1=dataset1.RasterXSize
    sizeY1=dataset1.RasterYSize
    dataset1=None

    bounds = [gt1[0], gt1[3], gt1[0] + (gt1[1] * sizeX1), gt1[3] + (gt1[5] * sizeY1)]
    logging.info(bounds)

    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(bounds[0], bounds[1])
    ring.AddPoint(bounds[2], bounds[1])
    ring.AddPoint(bounds[2], bounds[3])
    ring.AddPoint(bounds[0], bounds[3])
    ring.AddPoint(bounds[0], bounds[1])

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)

    return poly, srs1

def write_poly_to_shapefile(poly, shapefile_name, srs=None):
    driver = ogr.GetDriverByName('ESRI Shapefile')

    ds = driver.CreateDataSource(shapefile_name)
    layer = ds.CreateLayer("shape", srs, ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn('Name', ogr.OFTString))
    defn = layer.GetLayerDefn()

    # Create a new feature (attribute and geometry)
    feat = ogr.Feature(defn)
    feat.SetField('Name', 'shape')

    # Make a geometry
    wkt = poly.ExportToWkt()
    logging.debug("WKT: " + str(wkt))
    geom = ogr.CreateGeometryFromWkt(wkt)
    feat.SetGeometry(geom)

    layer.CreateFeature(feat)
    ds = layer = feat = geom = None

def get_raster_intersection(raster1,raster2):
    poly1, srs1 = get_raster_extent_as_poly(raster1)
    print "poly1", poly1

    poly2, srs2 = get_raster_extent_as_poly(raster2)
    print "poly2", poly2

    # convert poly2 into poly1 ProjectionRef
    transform = osr.CoordinateTransformation(srs2, srs1)
    poly2.Transform(transform)
    print "poly2 transformed", poly2

    intersection = poly2.Intersection(poly1)
    print "intersection", intersection

    #return also the srs in which is expressed the intersection
    return intersection, srs1

class snow_annual_map_evaluation(snow_annual_map):
    def __init__(self, params):
        self.params = params
        logging.info("Init snow_annual_map_evaluation")

        # inherit from snow_annual_map all the methods and variables
        snow_annual_map.__init__(self, params)

        self.l8_tile_id = params.get("l8_tile_id")
        self.l8_input_dir = str(params.get("l8_input_dir"))

        # Build useful paths
        self.l8_dates_filename = op.join(self.path_tmp, "l8_inputs_dates.txt")
        self.l8_multitemp_snow_vrt = op.join(self.path_tmp, "l8_multitemp_snow_mask.vrt")
        self.l8_multitemp_cloud_vrt = op.join(self.path_tmp, "l8_multitemp_cloud_mask.vrt")
        self.dem = params.get("dem")

        self.colorTable = gdal.ColorTable()
        self.colorTable.SetColorEntry(0, (14,124,0,255))
        self.colorTable.SetColorEntry(1, (206,30,30,255))
        self.colorTable.SetColorEntry(2, (252,255,30,255))
        self.colorTable.SetColorEntry(3, (30,30,233,255))
        self.colorTable.SetColorEntry(4, (0,0,0,255))

    def run_evaluation(self):
        logging.info("Run snow_annual_map_evaluation")

        # Set maximum ITK threads
        if self.nbThreads:
            os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(self.nbThreads)

        # search matching L8 snow product
        self.product_list = self.find_products(self.l8_input_dir, self.l8_tile_id)
        logging.debug("Product list:")
        logging.debug(self.product_list)

        # re-order products according acquisition date
        self.product_list.sort(key=lambda x: x.acquisition_date)
        logging.debug("Sorted product list:")
        logging.debug(self.product_list)

        # create the l8 products dates file
        l8_input_dates = []
        for product in self.product_list:
            l8_input_dates.append(datetime_to_str(product.acquisition_date))
        write_list_to_file(self.l8_dates_filename, l8_input_dates)

        # load required product
        self.snowmask_list = self.get_snow_masks()
        logging.debug("L8 snow mask list:")
        logging.debug(self.snowmask_list)

        # convert the snow masks into binary snow masks
        expression = "im1b1=="+self.label_cloud+"?2:(im1b1=="+self.label_no_data+"?2:(im1b1==" + self.label_snow + ")?1:0)"
        self.binary_snowmask_list = self.convert_mask_list(expression, "snow_eval")
        logging.debug("Binary snow mask list:")
        logging.debug(self.binary_snowmask_list)

        # pair the matching products
        ts_dates = read_list_from_file(self.output_dates_filename)
        pair_dict = {}
        for ts_index,ts_date in enumerate(ts_dates):
            for l8_index,l8_date in enumerate(l8_input_dates):
                if ts_date in l8_date:
                    pair_dict[l8_date] = (ts_index,l8_index)
        print pair_dict

        # project the snow masks onto the same foot print
        self.binary_snowmask_list_reprojected = []
        for mask_in in self.binary_snowmask_list:
            mask_out = mask_in.replace(".tif", "_reprojected.tif")
            if not os.path.exists(mask_out):
                super_impose_app = super_impose(self.annual_snow_map,
                                                mask_in,
                                                mask_out+GDAL_OPT_2B,
                                                "linear",
                                                2,
                                                self.ram,
                                                otb.ImagePixelType_uint8)
                super_impose_app.ExecuteAndWriteOutput()
                super_impose_app = None
            self.binary_snowmask_list_reprojected.append(mask_out)

        # compare the two snow masks
        comparision_list = []
        for l8_date in pair_dict.keys():
            s2_index,l8_index = pair_dict[l8_date]

            path_extracted = op.join(self.path_tmp, "gapfilled_s2_" + l8_date + ".tif")
            gdal.Translate(
                path_extracted,
                self.gapfilled_timeserie,
                format='GTiff',
                outputType=gdal.GDT_Byte,
                noData=None,
                bandList=[s2_index+1])

            expression = "im2b1==2?254:(2*im2b1+im1b1)"
            img_out = op.join(self.path_tmp, "comparision_" + l8_date + ".tif")
            bandMathApp = band_math([path_extracted,
                                     self.binary_snowmask_list_reprojected[l8_index]],
                                    img_out,
                                    expression,
                                    self.ram,
                                    otb.ImagePixelType_uint8)
            bandMathApp.ExecuteAndWriteOutput()
            bandMathApp = None
            comparision_list.append(img_out)

            # add color table
            apply_color_table(img_out, self.colorTable)
            shutil.copy2(img_out, self.path_out)

            out = op.join(self.path_tmp, "confusion_matrix_"+ l8_date + ".csv")
            confusionMatrixApp = confusion_matrix(
                                    path_extracted,
                                    self.binary_snowmask_list_reprojected[l8_index],
                                    out,
                                    2,
                                    self.ram)
            confusionMatrixApp.ExecuteAndWriteOutput()
            confusionMatrixApp = None

            shutil.copy2(out, self.path_out)

        # @TODO gather stats
        montage = op.join(self.path_tmp, "montage_comparison_L8.png")
        command = ["montage"]
        command.extend(["-label","%t"])
        command.extend(["-title", os.path.basename(self.path_out) + "_comparison_L8"])
        command.extend(["-geometry", "10%x10%+2+2", "-pointsize", "40"])
        command.extend(comparision_list)
        command.extend([montage])
        subprocess.call(command)
        logging.info("Command for comparison figure: " + " ".join(command))

        shutil.copy2(montage, self.path_out)

        #if self.mode == "DEBUG":
            #shutil.copytree(self.path_tmp, op.join(self.path_out, "tmpdir"))

        logging.info("End snow_annual_map_evaluation")

    def compare_modis(self):
        modis_snowserie = str(self.params.get("modis_snow_map"))
        modis_datefile = self.params.get("modis_snow_map_dates")

        self.modis_annual_snow_map = op.join(self.path_tmp, "modis_annual_snowmap.tif")

        modis_dates = read_list_from_file(modis_datefile)
        modis_start_index = None
        modis_stop_index = None
        for i in range(0,len(modis_dates)):
            tmp_date = str_to_datetime(modis_dates[i], "%Y,%m,%d")
            if tmp_date == self.date_start:
                modis_start_index = i
            if tmp_date == self.date_stop:
                modis_stop_index = i

        # generate the summary map
        band_index = range(modis_start_index+1,modis_stop_index+2)
        expression = "+".join(["(im1b" + str(i) + "==200?1:0)" for i in band_index])

        if not op.exists(self.modis_annual_snow_map):
            bandMathApp = band_math([modis_snowserie],
                                    self.modis_annual_snow_map,
                                    expression,
                                    self.ram,
                                    otb.ImagePixelType_uint16)
            bandMathApp.ExecuteAndWriteOutput()
            bandMathApp = None
        shutil.copy2(self.modis_annual_snow_map, self.path_out)

        # Compute intersection of the raster footprint
        intersection, srs = get_raster_intersection(self.annual_snow_map ,self.modis_annual_snow_map)

        # Export intersection as shapefile
        intersection_shapefile = op.join(self.path_tmp, "intersection.shp")
        write_poly_to_shapefile(intersection, intersection_shapefile, srs)

        # Crop to intersection S2 map
        s2_cropped = self.annual_snow_map.replace(".tif","_cropped.tif")
        gdal.Warp(s2_cropped,
                  self.annual_snow_map,
                  format='GTiff',
                  cutlineDSName=intersection_shapefile,
                  cropToCutline=True,
                  dstNodata=-1,
                  outputType=gdal.GDT_Int16)
        shutil.copy2(s2_cropped, self.path_out)

        # Crop to intersection MODIS map
        modis_cropped = self.modis_annual_snow_map.replace(".tif","_cropped.tif")
        gdal.Warp(modis_cropped,
                  self.modis_annual_snow_map,
                  format='GTiff',
                  cutlineDSName=intersection_shapefile,
                  cropToCutline=True,
                  dstNodata=-1,
                  outputType=gdal.GDT_Int16)
        shutil.copy2(modis_cropped, self.path_out)

        # Crop to intersection DEM
        dem_cropped = op.join(self.path_tmp, "dem_cropped.tif")
        gdal.Warp(dem_cropped,
                  self.dem,
                  format='GTiff',
                  cutlineDSName=intersection_shapefile,
                  cropToCutline=True,
                  dstNodata=-1,
                  outputType=gdal.GDT_Int16)
        shutil.copy2(dem_cropped, self.path_out)

        # Reproject the DEM onto MODIS footprint
        dem_cropped_reprojected = op.join(self.path_tmp, "dem_cropped_reprojected.tif")
        super_impose_app = super_impose(modis_cropped,
                                        dem_cropped,
                                        dem_cropped_reprojected,
                                        "bco",
                                        -1,
                                        self.ram,
                                        otb.ImagePixelType_int16)
        super_impose_app.ExecuteAndWriteOutput()
        super_impose_app = None
        shutil.copy2(dem_cropped_reprojected, self.path_out)

        compute_annual_stats(s2_cropped,
                             dem_cropped,
                             modis_cropped,
                             dem_cropped_reprojected,
                             self.path_out,
                             "intersection")

        # The following approach use super impose to project MODIS onto S2 data
        #for interp_method in ["linear"]:
            #modis_reprojected_snow_map = self.annual_snow_map.replace(".tif", "_reprojected_"+interp_method+".tif")
            #super_impose_app = super_impose(self.annual_snow_map,
                                            #self.modis_annual_snow_map,
                                            #modis_reprojected_snow_map,
                                            #interp_method,
                                            #-1,
                                            #self.ram,
                                            #otb.ImagePixelType_int16)
            #super_impose_app.ExecuteAndWriteOutput()
            #super_impose_app = None
            #shutil.copy2(modis_reprojected_snow_map, self.path_out)

            #compute_annual_stats(self.annual_snow_map,
                                 #self.dem,
                                 #modis_reprojected_snow_map,
                                 #self.dem,
                                 #self.path_out,
                                 #"superimpose")

        #if self.mode == "DEBUG":
            #shutil.copytree(self.path_tmp, op.join(self.path_out, "tmpdir"))


def compute_annual_stats(s2, dem_s2, modis, dem_modis, outputDir, suffix):
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    import numpy.ma as ma

    altitudes=[(0,500), (500,1000), (1000,1500), (1500,2000), (2000,10000)]

    s2_array = get_raster_as_array(s2)
    dem_s2_array = get_raster_as_array(dem_s2)
    modis_array = get_raster_as_array(modis)
    dem_modis_array = get_raster_as_array(dem_modis)

    s2_mask = (s2_array != -1)
    modis_mask = (modis_array != -1)

    if dem_modis == dem_s2:
        s2_mask &= modis_mask

    labels = []
    s2_data = []
    modis_data = []
    for alt_range in altitudes:
        logging.debug("Altitude stats for " + str(alt_range[0]) + "m - " + str(alt_range[1]) + "m")

        labels.append("["+str(alt_range[0])+"-"+str(alt_range[1])+"m[")

        indexes_s2 = np.where(s2_mask & (alt_range[0] <= dem_s2_array) & (dem_s2_array < alt_range[1]))
        s2_data.append(s2_array[indexes_s2])

        logging.debug(s2_data[-1].min())
        logging.debug(s2_data[-1].max())
        logging.debug(s2_data[-1].mean())
        logging.debug(s2_data[-1].var())

        indexes_modis = np.where(modis_mask & (alt_range[0] <= dem_modis_array) & (dem_modis_array < alt_range[1]))
        modis_data.append(modis_array[indexes_modis])

        logging.debug(modis_data[-1].min())
        logging.debug(modis_data[-1].max())
        logging.debug(modis_data[-1].mean())
        logging.debug(modis_data[-1].var())

    # box plots on one figure
    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 8), sharey=True)

    axes[0].boxplot(modis_data)
    axes[0].set_title("Modis")
    axes[0].xaxis.set_ticklabels(labels, rotation=-25)

    axes[1].boxplot(s2_data)
    axes[1].set_title("S2 estimated")
    axes[1].xaxis.set_ticklabels(labels, rotation=-25)

    output_figure = op.join(outputDir, "boxplot_MODIS_S2_" + suffix + ".png")
    plt.savefig(output_figure, bbox_inches="tight")

    # display
    # plt.show()

###############################################################
#   Main Test
###############################################################
def main():
    params = {"tile_id":"T31TCH",
              "date_start":"01/09/2015",
              "date_stop":"31/08/2016",
              "date_margin":15,
              "mode":"DEBUG",
              "input_dir":"/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/T31TCH",
              "path_tmp":os.environ['TMPDIR'],
              "path_out":"/home/qt/salguesg/scratch/workdir",
              "ram":4096,
              "nbThreads":8,
              "l8_tile_id":"D0005H0001",
              "l8_input_dir":"/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/Landsat-8/D0005H0001",
              "run_l8_evaluation":True,
              "run_modis_comparison":True,
              "modis_snow_map":"/home/qt/salguesg/scratch/workdir/MODIS/Pirineos_gapfilled.tif",
              "modis_snow_map_dates":"/home/qt/salguesg/scratch/workdir/MODIS/Pirineos_gapfilled_dates.csv",
              "dem":"/work/OT/siaa/Theia/Neige/DEM/S2__TEST_AUX_REFDE2_T31TCH_0001.DBL.DIR/S2__TEST_AUX_REFDE2_T31TCH_0001_ALT_R2.TIF"}

    #params = {"tile_id":"T32TLS",
              #"date_start":"01/09/2015",
              #"date_stop":"31/08/2016",
              #"mode":"DEBUG",
              #"input_dir":"/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/T32TLS",
              #"path_tmp":os.environ['TMPDIR'],
              #"path_out":"/home/qt/salguesg/scratch/workdir",
              #"ram":4096,
              #"nbThreads":8,
              #"run_l8_evaluation":True,
              #"run_modis_comparison":True,
              #"l8_tile_id":"D0010H0005",
              #"l8_input_dir":"/work/OT/siaa/Theia/Neige/output_muscate_v2pass2red40/Landsat-8/N2A_France-MetropoleD0010H0005",
              #"modis_snow_map":"/home/qt/salguesg/scratch/workdir/MODIS/Alpes_gapfilled.tif",
              #"modis_snow_map_dates":"/home/qt/salguesg/scratch/workdir/MODIS/Alpes_gapfilled_dates.csv",
              #"dem":"/work/OT/siaa/Theia/Neige/DEM/S2__TEST_AUX_REFDE2_T32TLS_0001.DBL.DIR/S2__TEST_AUX_REFDE2_T32TLS_0001_ALT_R2.TIF"}

    snow_annual_map_evaluation_app = snow_annual_map_evaluation(params)
    snow_annual_map_evaluation_app.run()
    #snow_annual_map_evaluation_app.run_evaluation()
    #snow_annual_map_evaluation_app.compare_modis()

if __name__ == '__main__':
    # Set logging level and format.
    logging.basicConfig(level=logging.DEBUG, format=\
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()

