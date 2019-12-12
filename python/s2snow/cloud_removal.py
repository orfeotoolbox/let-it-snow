#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import multiprocessing
import csv
import numpy as np
import matplotlib.pyplot as plot
from subprocess import call
import os.path as op
import gdal
import gdalconst


def show_help():
    print("This script is used to remove clouds from snow data")
    print("Usage: cloud_removal.py config.json")


def get_raster_as_array(raster_file_name):
    dataset = gdal.Open(raster_file_name, gdalconst.GA_ReadOnly)
    wide = dataset.RasterXSize
    high = dataset.RasterYSize
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray(0, 0, wide, high)
    return array, dataset


def set_array_as_raster(array, dataset, output_path):
    high, wide = array.shape
    output = gdal.GetDriverByName('GTiff').Create(
        output_path, wide, high, 1, gdal.GDT_Byte)
    output.GetRasterBand(1).WriteArray(array)

    # georeference the image and set the projection
    output.SetGeoTransform(dataset.GetGeoTransform())
    output.SetProjection(dataset.GetProjection())
    output = None


def compute_HSmin(image_path, dem_path):
    array_image, dataset_image = get_raster_as_array(image_path)
    array_dem, dataset_dem = get_raster_as_array(dem_path)

    return array_dem[array_image == 100].min()


def compute_HSmax(image_path, dem_path):
    array_image, dataset_image = get_raster_as_array(image_path)
    array_dem, dataset_dem = get_raster_as_array(dem_path)

    elev_max_nosnow = array_dem[array_image == 0].max()
    return array_dem[(array_image == 100) & (
        array_dem > elev_max_nosnow)].min()


def compute_cloudpercent(image_path):
    array_image, dataset_image = get_raster_as_array(image_path)
    cloud = np.sum(array_image == 205)
    tot_pix = np.sum(array_image != 254)
    return (float(cloud) / float(tot_pix)) * 100


def compute_cloud(image):
    array, dataset = get_raster_as_array(image)
    msk_cloud = (array == 205)
    return np.sum(msk_cloud)


def step1(m2_path, m1_path, t0_path, p1_path, p2_path, output_path, ram):

    # Cloud conditions (include pixel flagged as cloud and also as no data
    cloud_nodata_condition = "(im2b1 == 205 || im2b1 == 254)"

    # S(y,x,t) = 1 if (S(y,x,t-1) = 1 and S(y,x,t+1) = 1)
    call(
        [
            "otbcli_BandMath",
            "-ram",
            str(ram),
            "-il",
            m1_path,
            t0_path,
            p1_path,
            "-out",
            output_path,
            "-exp",
            cloud_nodata_condition +
            "?((im1b1==100&&im3b1==100)?100:(im1b1==0&&im3b1==0?0:im2b1)):im2b1"])
    # S(y,x,t) = 1 if (S(y,x,t-2) = 1 and S(y,x,t+1) = 1)
    call(
        [
            "otbcli_BandMath",
            "-ram",
            str(ram),
            "-il",
            m2_path,
            output_path,
            p1_path,
            "-out",
            output_path,
            "-exp",
            cloud_nodata_condition +
            "?((im1b1==100&&im3b1==100)?100:(im1b1==0&&im3b1==0?0:im2b1)):im2b1"])
    # S(y,x,t) = 1 if (S(y,x,t-1) = 1 and S(y,x,t+2) = 1)
    call(
        [
            "otbcli_BandMath",
            "-ram",
            str(ram),
            "-il",
            m1_path,
            output_path,
            p2_path,
            "-out",
            output_path,
            "-exp",
            cloud_nodata_condition +
            "?((im1b1==100&&im3b1==100)?100:(im1b1==0&&im3b1==0?0:im2b1)):im2b1"])


def step2(t0_path, dem_path, output_path, ram):

    percentage_cloud = compute_cloudpercent(t0_path)
    print("cloud percent : " + str(percentage_cloud))

    # Perform step 2 only if cloud coverage is less than a threshold value
    # (hard coded for now to 30%)
    cloudpercent_condition = percentage_cloud < 30

    if cloudpercent_condition:
        # S(y,x,t) = 1 if (H(x,y) < Hsmin(t))
        hs_min = compute_HSmin(t0_path, dem_path)
        print("hs_min: " + str(hs_min))
        call(["otbcli_BandMath",
              "-ram",
              str(ram),
              "-il",
              t0_path,
              dem_path,
              "-out",
              output_path,
              "-exp",
              "im1b1==205?(im2b1<" + str(hs_min) + "?0:im1b1):im1b1"])
        hs_max = compute_HSmax(t0_path, dem_path)
        print("hs_max: " + str(hs_max))
        # S(y,x,t) = 1 if (H(x,y) > Hsmax(t))
        call(["otbcli_BandMath",
              "-ram",
              str(ram),
              "-il",
              output_path,
              dem_path,
              "-out",
              output_path,
              "-exp",
              "im1b1==205?(im2b1>" + str(hs_max) + "?100:im1b1):im1b1"])

    return cloudpercent_condition


def step3(t0_path, output_path):

    # four-pixels neighboring
    print("Starting step 3")
    array, dataset = get_raster_as_array(t0_path)

    # compute 4 pixel snow neighboring
    step3_internal(array)

    set_array_as_raster(array, dataset, output_path)
    # create file
    print("End of step 3")


def step3_internal(array):
    # Get west, north, east & south elements for [1:-1,1:-1] region of input
    # array
    W = array[1:-1, :-2]
    N = array[:-2, 1:-1]
    E = array[1:-1, 2:]
    S = array[2:, 1:-1]

    # Check if all four arrays have 100 for that same element in that region
    mask = (W == 100) & (N == 100) & (E == 100) & (
        S == 100) & (array[1:-1, 1:-1] == 205)

    # Use the mask to set corresponding elements
    array[1:-1, 1:-1][mask] = 100


def step4(t0_path, dem_path, output_path):
    # S(y,x,t) = 1 if (S(y+k,x+k,t)(kc(-1,1)) = 1 and H(y+k,x+k)(kc(-1,1)) <
    # H(y,x))
    print("Starting step 4")
    array, dataset = get_raster_as_array(t0_path)
    array_dem, dataset_dem = get_raster_as_array(dem_path)

    # step5
    step4_internal(array, array_dem)

    # create file
    set_array_as_raster(array, dataset, output_path)
    print("End of step 4")


def step4_internal(array, array_dem):
    # Get 8 neighboring pixels for raster and dem
    W = array[1:-1, :-2]
    NW = array[:-2, :-2]
    N = array[:-2, 1:-1]
    NE = array[:-2, 2:]
    E = array[1:-1, 2:]
    SE = array[2:, 2:]
    S = array[2:, 1:-1]
    SW = array[2:, :-2]

    Wdem = array_dem[1:-1, :-2]
    NWdem = array_dem[:-2, :-2]
    Ndem = array_dem[:-2, 1:-1]
    NEdem = array_dem[:-2, 2:]
    Edem = array_dem[1:-1, 2:]
    SEdem = array_dem[2:, 2:]
    Sdem = array_dem[2:, 1:-1]
    SWdem = array_dem[2:, :-2]

    arrdem = array_dem[1:-1, 1:-1]
    mask = (
        (((W == 100) & (
            arrdem > Wdem)) | (
            (N == 100) & (
                arrdem > Ndem)) | (
                    (E == 100) & (
                        arrdem > Edem)) | (
                            (S == 100) & (
                                arrdem > Sdem)) | (
                                    (NW == 100) & (
                                        arrdem > NWdem)) | (
                                            (NE == 100) & (
                                                arrdem > NEdem)) | (
                                                    (SE == 100) & (
                                                        arrdem > SEdem)) | (
                                                            (SW == 100) & (
                                                                arrdem > SWdem))) & (
                                                                    array[
                                                                        1:-1, 1:-1] == 205))

    # Use the mask to set corresponding elements
    array[1:-1, 1:-1][mask] = 100


def compute_stats(image, image_relative, image_reference):
    array, dataset = get_raster_as_array(image)
    array_relative, dataset = get_raster_as_array(image_relative)
    array_reference, dataset = get_raster_as_array(image_reference)
    return compute_stats_internal(array, array_relative, array_reference)


def compute_stats_internal(array, array_relative, array_reference):
    # Relative Cloud Elimination
    msk_cloud_elim = (
        array_relative == 205) & (
        array != 205) & (
            array_reference != 205)
    cloud_elim = np.sum(msk_cloud_elim)
    # Various stats from paper
    # TODO Facto
    msk_StoS = (
        array == 100) & (
        array_reference == 100) & (
            array_relative == 205)
    msk_LtoL = (array == 0) & (array_reference == 0) & (array_relative == 205)
    msk_StoL = (
        array == 0) & (
        array_reference == 100) & (
            array_relative == 205)
    msk_LtoS = (
        array == 100) & (
        array_reference == 0) & (
            array_relative == 205)

    StoS = np.sum(msk_StoS)
    LtoL = np.sum(msk_LtoL)
    StoL = np.sum(msk_StoL)
    LtoS = np.sum(msk_LtoS)

    TRUE = StoS + LtoL
    FALSE = StoL + LtoS

    # return all the result
    return cloud_elim, TRUE, FALSE, StoS, LtoL, StoL, LtoS
# Set percentage based on the cloud removal percent


def format_percent(array, total_cloud):
    # TODO FACTO
    stats_array_percent = np.copy(array.astype(float))
    # divide by zero => value set to 0
    with np.errstate(divide='ignore', invalid='ignore'):
        stats_array_percent[:, 6] = np.divide(
            stats_array_percent[:, 6], stats_array_percent[:, 2])
        stats_array_percent[:, 5] = np.divide(
            stats_array_percent[:, 5], stats_array_percent[:, 2])
        stats_array_percent[:, 4] = np.divide(
            stats_array_percent[:, 4], stats_array_percent[:, 1])
        stats_array_percent[:, 3] = np.divide(
            stats_array_percent[:, 3], stats_array_percent[:, 1])
        stats_array_percent[:, 2] = np.divide(
            stats_array_percent[:, 2], stats_array_percent[:, 0])
        stats_array_percent[:, 1] = np.divide(
            stats_array_percent[:, 1], stats_array_percent[:, 0])
        stats_array_percent[~np.isfinite(
            stats_array_percent)] = 0  # prevents nan

    stats_array_percent[:, 0] /= total_cloud
    stats_array_percent[:, 1] = np.multiply(
        stats_array_percent[:, 1], stats_array_percent[:, 0])
    stats_array_percent[:, 2] = np.multiply(
        stats_array_percent[:, 2], stats_array_percent[:, 0])
    stats_array_percent[:, 3] = np.multiply(
        stats_array_percent[:, 3], stats_array_percent[:, 1])
    stats_array_percent[:, 4] = np.multiply(
        stats_array_percent[:, 4], stats_array_percent[:, 1])
    stats_array_percent[:, 5] = np.multiply(
        stats_array_percent[:, 5], stats_array_percent[:, 2])
    stats_array_percent[:, 6] = np.multiply(
        stats_array_percent[:, 6], stats_array_percent[:, 2])

    stats_array_percent *= 100
    return stats_array_percent


def plot_stats(array):
    steps = list(range(0, array.shape[0]))
    TCE = array[:, 0]
    TRUE = array[:, 1]
    FALSE = array[:, 2]
    StoS = array[:, 3]
    LtoL = array[:, 4]
    StoL = array[:, 5]
    LtoS = array[:, 6]
    plot.plot(steps, TCE, TRUE, FALSE, StoS, LtoL, StoL, LtoS)
    plot.show()


def run(data):

    general = data["general"]
    output_path = general.get("pout")
    ram = general.get("ram", 512)
    stats = general.get("stats", False)

    try:
        nb_defaultThreads = multiprocessing.cpu_count()
    except NotImplementedError:
        print("Cannot get max number of CPU on the system. nbDefaultThreads set to 1.")
        nb_defaultThreads = 1

    nb_threads = general.get("nb_threads", nb_defaultThreads)
    os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"] = str(nb_threads)

    inputs = data["inputs"]
    m2_path = inputs.get("m2Path")
    m1_path = inputs.get("m1Path")
    t0_path = inputs.get("t0Path")
    p1_path = inputs.get("p1Path")
    p2_path = inputs.get("p2Path")
    dem_path = inputs.get("demPath")
    ref_path = inputs.get("refPath", "norefpath")
    # parameters=data["parameters"]
    # hs_min=parameters.get("hsMin")
    # hs_max=parameters.get("hsMax")
    # window_size=parameters.get("windowSize")

    steps = data["steps"]
    s1 = steps.get("s1", True)
    s2 = steps.get("s2", True)
    s3 = steps.get("s3", True)
    s4 = steps.get("s4", True)

    statsarr = []

    # TODO FACTO. Generic step ? arg function
    latest_file_path = t0_path
    if s1:
        temp_output_path = op.join(
            output_path, "cloud_removal_output_step1.tif")
        step1(
            m2_path,
            m1_path,
            latest_file_path,
            p1_path,
            p2_path,
            temp_output_path,
            ram)
        if stats:
            statsarr.append(
                compute_stats(
                    temp_output_path,
                    latest_file_path,
                    ref_path))
        latest_file_path = temp_output_path
    if s2:
        temp_output_path = op.join(
            output_path, "cloud_removal_output_step2.tif")
        cloudpercent = step2(latest_file_path, dem_path, temp_output_path, ram)

        # Step 2 is only perform if cloud percent is lower than a threshold
        # (conditional step)
        if cloudpercent:
            latest_file_path = temp_output_path
            if stats:
                statsarr.append(
                    compute_stats(
                        temp_output_path,
                        latest_file_path,
                        ref_path))

    if s3:
        temp_output_path = op.join(
            output_path, "cloud_removal_output_step3.tif")
        step3(latest_file_path, temp_output_path)
        if stats:
            statsarr.append(
                compute_stats(
                    temp_output_path,
                    latest_file_path,
                    ref_path))
        latest_file_path = temp_output_path
    if s4:
        temp_output_path = op.join(
            output_path, "cloud_removal_output_step4.tif")
        step4(latest_file_path, dem_path, temp_output_path)
        if stats:
            statsarr.append(
                compute_stats(
                    temp_output_path,
                    latest_file_path,
                    ref_path))
        latest_file_path = temp_output_path

    if stats:
        stats_array = np.array(statsarr)
        stats_array_percent = format_percent(
            stats_array, compute_cloud(t0_path))
        stats_array = np.vstack([stats_array, np.sum(
            stats_array, axis=0)])  # add total to array
        stats_array_percent = np.vstack([stats_array_percent, np.sum(
            stats_array_percent, axis=0)])  # add total to array

        print(stats_array)
        np.set_printoptions(precision=3)
        np.set_printoptions(suppress=True)
        print(stats_array_percent)

        # plot_stats(stats_array)

        # Python list supported not numpy array
        statsabs = stats_array.tolist()
        statsf = open('stats.json', 'w')
        json.dump(statsabs, statsf)
        statsf.close()

        statsp = stats_array_percent.tolist()
        statspf = open('stats_percent.json', 'w')
        json.dump(statsp, statspf)
        statspf.close()


def main(argv):
    run(argv)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        show_help()
    else:
        main(sys.argv)
