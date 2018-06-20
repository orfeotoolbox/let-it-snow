#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import os.path as op
from lxml import etree

def main(argv):
	minsnowthreshold = argv[1]
	maxsnowthreshold = argv[2]
	mincloudthreshold = argv[3]
	maxcloudthreshold = argv[4]
	
	total_images = 0
	
	for root, dirs, files in os.walk("."):
		for name in files:
			if name == "metadata.xml":
				tree = etree.parse(op.join(root, name))
				snow_percent = float(tree.find("./Global_Index_List/QUALITY_INDEX/[@name='SnowPercent']").text)
				cloud_percent = float(tree.find("./Global_Index_List/QUALITY_INDEX/[@name='CloudPercent']").text)
				
				# Find potential
				if snow_percent > minsnowthreshold and cloud_percent > mincloudthreshold and snow_percent < maxsnowthreshold and cloud_percent < maxcloudthreshold :
					print root
					print "snow percent: " + str(snow_percent)
					print "cloud percent: " + str(cloud_percent)
					total_images += 1
					
	print "total images :" + str(total_images)

if __name__ == "__main__":
	if len(sys.argv) != 5:
		print "Missing arguments"
	else:
		main(sys.argv)
