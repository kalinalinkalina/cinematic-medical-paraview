import pyopenvdb
import os
import sys
import numpy

# Change these variables
in_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/npy/"
out_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/vdb/"
file_name = "exhalation_subjB_cyc3"
spacing = [4,1.367188,1.367188] #or [1.367188, 1.367188, 4]; the lung2npy.py script will print out what the spacing should be

# Read the data
arr = numpy.load(in_folder + file_name + ".npy")

# Copy data from array into OpenVDB
vdb = pyopenvdb.FloatGrid()
vdb.copyFromArray(arr) 
vdb.name = "density"

# Transform the volume
xform = [[spacing[0],0,0,0],[0,spacing[1],0,0],[0,0,spacing[2],0],[0,0,0,1]]
vdb.transform = pyopenvdb.createLinearTransform(matrix=xform)

# Write out in OpenVDB format
pyopenvdb.write(out_folder + file_name + ".vdb", grids=[vdb])
