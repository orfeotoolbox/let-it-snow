#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging

from s2snow.snow_detector import compute_cloud_mask

def main(argv):
    app = compute_cloud_mask(argv[1],
                             argv[3],
                             argv[2])
    if app is None:
        sys.exit(1)
    else:
        sys.exit(app.ExecuteAndWriteOutput())

if __name__ == "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')

    main(sys.argv)
