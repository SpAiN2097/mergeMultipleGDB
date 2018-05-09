# -*- coding: utf-8 -*-
import arcpy
import os
import re

# Set input and output directories here
inws = r'E:\DLG\gdb'
outws = r'E:\DLG\gdb1'
pattern_gdb = re.compile(".gdb$")

# helper functions
def locate_file(pattern, root= "."):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.
    
    Modified based on http://code.activestate.com/recipes/499305-locating-files-throughout-a-directory-tree/
    '''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for file in files:
            if re.search(pattern, file):
                yield os.path.join(path, file)
                
def locate_dir(pattern, root= "."):
    '''Locate all files matching supplied filename pattern in and below
    supplied root directory.
    
    Modified based on http://code.activestate.com/recipes/499305-locating-files-throughout-a-directory-tree/
    '''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for d in dirs:
            if re.search(pattern, d):
                yield os.path.join(path, d)


gdbs = [] # store all mdb files' absolut path.
for g in locate_dir(pattern_gdb, root=inws):
    gdbs.append(g)

# The following codes modified from https://gis.stackexchange.com/questions/156708/copying-feature-classes-from-personal-geodatabase-to-file-geodatabase-using-arcp
# Define output FGDB name
fgdb_name = "merged.gdb"
# print("New file geodatabase:", fgdb_name)

# Create a new FGDB, make sure this file geodatabase dosn't exist when running this script.
arcpy.CreateFileGDB_management(outws, fgdb_name)

count = 0
for g in gdbs:
    # Create a dict, with keys of feature class names directly in file geodatabases.
    direct_fcs = {}

    # Add any FCs that are directly in file geodatabase to the dict.
    arcpy.env.workspace = os.path.join(inws, g)  
    fcs = arcpy.ListFeatureClasses()
    for fc in fcs:
        direct_fcs.get(fc, []).append(os.path.join(inws, g, fc))
        # print("Feature class directly in file geodatabase: ", fc)

    # List the feature dataset, directly in personal geodatabase
    arcpy.env.workspace = os.path.join(inws, g)
    fds = arcpy.ListDatasets()
    for f in fds:
        # print("Dataset: ", f)
        # Reset the working space to personal geodatabase, which maybe changed to last dataset in last loop.
        arcpy.env.workspace = os.path.join(inws, g) 
        # Determine FDS spatial reference
        desc = arcpy.Describe(f)
        sr = desc.spatialReference
        # print("Spatial reference: ", sr)

        # Copy FDS to FGDB, create dataset in file geodataset with the same spatial reference
        arcpy.CreateFeatureDataset_management(os.path.join(outws, fgdb_name), f, spatial_reference = sr)

        # Copy the FCs to new FDS
        arcpy.env.workspace = os.path.join(inws, g, f) # set workspace to the dataset in input personal geodatabase
        # print("Workspace directly in dataset: ", arcpy.env.workspace)
        fcs = arcpy.ListFeatureClasses()
        for fc in fcs:
            arcpy.CopyFeatures_management(fc, os.path.join(outws, fgdb_name, f, fc))
            # print("Feature class: ", fc)
        
    # Report on processing status
    print("%s of %s personal databases converted to FGDB" % (count, len(gdbs)))
    count += 1
