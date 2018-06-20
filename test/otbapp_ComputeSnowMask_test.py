#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

from s2snow.snow_detector import compute_snow_mask

def main(argv):
    app = compute_snow_mask(argv[1],
                            argv[2],
                            argv[3],
                            argv[4],
                            argv[5])
    if app is None:
        sys.exit(1)
    else:
        sys.exit(app.ExecuteAndWriteOutput())

if __name__ == "__main__":
    # Set logging level and format.
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    
    main(sys.argv)
