#!/usr/bin/python
import os
import re
import sys
import json
import logging

### Configuration Template ###
conf_template={"general":{
                        "pout":"",
                        "nodata":-10000,
                        "ram":1024,
                        "nb_threads":1,
                        "generate_vector":False,
                        "preprocessing":False,
                        "log":True,
                        "multi":1
                        },
               "inputs":{
                        "green_band":{
                                    "path": "",
                                    "noBand": 1
                                    },
                        "red_band":{
                                    "path": "",
                                    "noBand": 1
                                    },
                        "swir_band":{
                                    "path": "",
                                    "noBand": 1
                                    },
                        "dem":"",
                        "cloud_mask":""
                        },
               "snow":{
                        "dz":100,
                        "ndsi_pass1":0.4,
                        "red_pass1":200,
                        "ndsi_pass2":0.15,
                        "red_pass2":120,
                        "fsnow_lim":0.1,
                        "fsnow_total_lim":0.001
                        },
               "cloud":{
                        "shadow_in_mask":64,
                        "shadow_out_mask":128,
                        "all_cloud_mask":1,
                        "high_cloud_mask":32,
                        "rf":12,
                        "red_darkcloud":500,
                        "red_backtocloud":100
                        }
                }

### Mission Specific Parameters ###
S2_parameters={"multi":10,
               "green_band":".*FRE_B3.*\.tif$",
               "green_bandNumber":1,
               "red_band":".*FRE_B4.*\.tif$",
               "red_bandNumber":1,
               "swir_band":".*FRE_B11.*\.tif$",
               "swir_bandNumber":1,
               "cloud_mask":".*CLM_R2\.tif$",
               "dem":".*ALT_R2\.TIF$",
               "shadow_in_mask":32,
               "shadow_out_mask":64,
               "all_cloud_mask":1,
               "high_cloud_mask":128,
               "rf":12}

Take5_parameters={"multi":1,
                  "green_band":".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                  "green_bandNumber":1,
                  "red_band":".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                  "red_bandNumber":2,
                  "swir_band":".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
                  "swir_bandNumber":4,
                  "cloud_mask":".*NUA.*\.TIF$",
                  "dem":".*\.tif",
                  "shadow_in_mask":64,
                  "shadow_out_mask":128,
                  "all_cloud_mask":1,
                  "high_cloud_mask":32,
                  "rf":8}

L8_parameters={"multi":1,
               "green_band":".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
               "green_bandNumber":3,
               "red_band":".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
               "red_bandNumber":4,
               "swir_band":".*ORTHO_SURF_CORR_PENTE.*\.TIF$",
               "swir_bandNumber":6,
               "cloud_mask":".*NUA.*\.TIF$",
               "dem":".*\.tif",
               "shadow_in_mask":64,
               "shadow_out_mask":128,
               "all_cloud_mask":1,
               "high_cloud_mask":32,
               "rf":8}

mission_parameters = {"S2":S2_parameters,"LANDSAT8":L8_parameters,"Take5":Take5_parameters}

def findFiles(folder,pattern):
    matches=[]
    for root, dirs, files in os.walk(folder):
        for file in files:
            if re.match(pattern, file):
                matches.append(os.path.join(root, file))
    return matches

def read_product(dataPath, mission):

    if os.path.exists(dataPath):
        params = mission_parameters[mission]
        conf_json = conf_template

        conf_json["general"]["multi"] = params["multi"]

        conf_json["inputs"]["green_band"]["path"] = findFiles(dataPath, params["green_band"])[0]
        conf_json["inputs"]["red_band"]["path"] = findFiles(dataPath, params["red_band"])[0]
        conf_json["inputs"]["swir_band"]["path"] = findFiles(dataPath, params["swir_band"])[0]
        conf_json["inputs"]["green_band"]["noBand"] = params["green_bandNumber"]
        conf_json["inputs"]["red_band"]["noBand"] = params["red_bandNumber"]
        conf_json["inputs"]["swir_band"]["noBand"] = params["swir_bandNumber"]
        conf_json["inputs"]["cloud_mask"] = findFiles(dataPath, params["cloud_mask"])[0]
        result = findFiles(os.path.join(dataPath,"SRTM"), params["dem"])
        if result:
            conf_json["inputs"]["dem"] = result[0]

        conf_json["cloud"]["shadow_in_mask"] = params["shadow_in_mask"]
        conf_json["cloud"]["shadow_out_mask"] = params["shadow_out_mask"]
        conf_json["cloud"]["all_cloud_mask"] = params["all_cloud_mask"]
        conf_json["cloud"]["high_cloud_mask"] = params["high_cloud_mask"]
        conf_json["cloud"]["rf"] = params["rf"]

        return conf_json
    else:
        logging.error(dataPath + " doesn't exist.")

def show_help():
    print "This script is used to generate the snow detector configuration file"
    print "Usage: test_json_builder.py <product_path> <output_path>"
    print "Supported products: S2/L8/Take5"

def main(argv):

    # parse arguments
    dataPath = argv[1]
    outputPath = argv[2]

    if "S2" in dataPath:
        jsonData = read_product(dataPath,"S2")
    elif "Take5" in dataPath:
        jsonData = read_product(dataPath,"Take5")
    elif "LANDSAT8" in dataPath:
        jsonData = read_product(dataPath,"LANDSAT8")
    else:
        logging.error("Unknown product type.")

    if not os.path.exists(outputPath):
        os.makedirs(outputPath)

    jsonData["general"]["pout"] = outputPath

    jsonFile = open(os.path.join(outputPath,"param_test.json"), "w")
    jsonFile.write(json.dumps(jsonData, indent=4))
    jsonFile.close()

if __name__ == "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')

    if len(sys.argv) != 3:
        show_help()
    else:
        main(sys.argv)
