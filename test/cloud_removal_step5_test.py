#!/usr/bin/env python

import sys 
import numpy as np
from s2snow import cloud_removal

arr = np.array([205, 100, 205, 205,
				205, 205, 100, 100,
				100, 205, 205, 255,
				205, 205, 205, 100]).reshape(4,4)

arrdem = np.array([1, 0, 0, 0,
				   0, 0, 1, 0,
				   0, 0, 0, 1,
				   0, 0, 1, 0]).reshape(4,4)


cloud_removal.step5_internal(arr, arrdem)

expected = np.array([100, 100, 205, 205,
					 205, 205, 100, 100,
					 100, 205, 205, 255,
					 205, 205, 100, 100]).reshape(4,4)
