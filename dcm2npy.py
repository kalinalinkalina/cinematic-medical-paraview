import pydicom
import os
import sys
import numpy

# Specify the path locations
in_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/data_all_subj/images/"
out_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/npy/"
file_name = "exhalation_subjB_cyc3"

# Read the file
f = pydicom.dcmread(in_folder + file_name + ".dcm")

# Extract the dimensions and spacing information
spacing = (f.PixelSpacing[0], f.PixelSpacing[1], f.SliceThickness)
arr = f.pixel_array
res = arr.shape

# Print out the spacing, for reference and for use in npy2vdb.py script
print("Spacing = " + str(spacing))

# Create a blank 3D grid (array) to hold the data
arr = numpy.zeros(res) 

# Store the data in numpy format
numpy.save(out_folder + file_name + ".npy", arr)
