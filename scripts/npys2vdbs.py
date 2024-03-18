
import pyopenvdb
import os
import sys
import numpy

in_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/npy/"
out_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/vdb/"
file_name = "sl014"


for i in range(200):
	arr = numpy.load( ("%s%s.%03d.npy" % (in_folder, file_name, i) ) )
	arr_float = arr.astype(float) 

	# Copy data from array into OpenVDB
	vdb = pyopenvdb.FloatGrid()
	vdb.copyFromArray(arr_float) 
	vdb.name = "density"

	# Transform the volume
	spacing = [1.205, 1.205, 5]
	xform = [[spacing[0],0,0,0],[0,spacing[1],0,0],[0,0,spacing[2],0],[0,0,0,1]]
	vdb.transform = pyopenvdb.createLinearTransform(matrix=xform)

	pyopenvdb.write("%s%s.%03d.vdb" % (out_folder, file_name, i), grids=[vdb])
