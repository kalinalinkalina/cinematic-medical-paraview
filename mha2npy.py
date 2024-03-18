import SimpleITK as sitk
import os
import sys
import numpy

# Specify the path locations
in_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/sl014/timesteps/"
out_folder = "/Users/kalina/Code/cs6635/finalProj/Lungs/npy/"
file_name = "sl014"

# Create a list of all of the files in the folder
all_file_names = os.listdir(in_folder)

# Sort the file names
all_file_names.sort()

# Read the files
for i in range(len(all_file_names)):
	f = sitk.ReadImage(in_folder + all_file_names[i])
	#spacing = f.GetSpacing()
	arr = sitk.GetArrayFromImage(f)
	numpy.save("%s%s.%03d.npy" % (out_folder, file_name, i), arr)


