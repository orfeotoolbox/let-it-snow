#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#=========================================================================
#
#  Program:   lis
#  Language:  Python
#
#  Copyright (c) Simon Gascoin
#  Copyright (c) Manuel Grizonnet
#
#  See lis-copyright.txt for details.
#
#  This software is distributed WITHOUT ANY WARRANTY; without even
#  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the above copyright notices for more information.
#
#=========================================================================

from __future__ import print_function
import os
import sys
import argparse
from s2snow import snow_detector
import json

def main(argv):

    print(argv)

    json_file = argv[0]
    snow_mask = argv[1]
    cloud_mask = argv[2]

    # Load json_file from json files
    with open(json_file) as json_data_file:
        data = json.load(json_data_file)

    #dummy json
    sd = snow_detector.snow_detector(data)

    #
    sd.pass1_5(snow_mask, cloud_mask, 1, 0.85)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
