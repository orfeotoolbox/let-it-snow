#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys 
import numpy as np
from s2snow import cloud_removal

arr = np.array([255, 255, 255, 255, 255,
				205, 100, 205, 100, 255,
				100, 205, 100, 100, 205,
				255, 100, 100, 205, 100,
				255, 255, 255, 255, 100]).reshape(5,5)

cloud_removal.step3_internal(arr)

expected = np.array([255, 255, 255, 255, 255,
					 205, 100, 205, 100, 255,
					 100, 100, 100, 100, 205,
					 255, 100, 100, 205, 100,
					 255, 255, 255, 255, 100]).reshape(5,5)

if((arr==expected).all()):
	sys.exit(0)
else:
	sys.exit(1)
