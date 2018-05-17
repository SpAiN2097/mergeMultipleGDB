# -*- coding: utf-8 -*-
import arcpy
import os
import re
import pandas as pd

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
                
def getFCDomainUnion(gdbs):
    """
    Get the union of all the sr.domain of all Feature classes directly in every gdbs.
    
    Arg: a list of gdbs.
    Return: a tuple of (xmin, ymin, xmax, ymax)
    
    """
    li_domain = []
    for g in gdbs:
        arcpy.env.workspace = os.path.join(inws, g)
        fcs = arcpy.ListFeatureClasses()
        for fc in fcs:
            desc = arcpy.Describe(fc)
            sr = desc.spatialReference
            # Notice that sr.domain get a string of (xmin, ymin, xmax, ymax) separated by a space.
            li_domain.append([float(x) for x in sr.domain.split(" ")])
    df = pd.DataFrame(li_domain)
    return (df.iloc[:, 0].min(), df.iloc[:, 1].min(), df.iloc[:, 2].max(), df.iloc[:, 3].max())


if __name__ == '__main__':
    # Set input and output directories here
    inws = r'E:\DLG\gdb'
    outws = r'E:\DLG\gdb_merge1'
    pattern_gdb = re.compile(".gdb$")
    gdbs = [] # store all gdb files' absolut path, which has a dataset level.
    for g in locate_dir(pattern_gdb, root=inws):
        gdbs.append(g)

    # Define output FGDB name
    fgdb_name = "merged_no_ds.gdb"

    # Create a new FGDB
    # Make sure this file geodatabase dosn't exist before running this script.
    arcpy.CreateFileGDB_management(outws, fgdb_name)

    xmin, ymin, xmax, ymax = getFCDomainUnion(gdbs)

    g = gdbs[0]
    arcpy.env.workspace = os.path.join(inws, g)
    fcs = arcpy.ListFeatureClasses()
    fc = fcs[0]
    desc = arcpy.Describe(fc)
    sr = desc.spatialReference

    # http://pro.arcgis.com/zh-cn/pro-app/arcpy/classes/spatialreference.htm
    # update the domain of x and y to the union of all feature classes from every gdbs.
    # Notice that when we set the domain of spatialReference, the sequence is: xmin, xmax, ymin, ymax, which is different
    # from the sequence what we get from sr.domain. setDomain (x_min, x_max, y_min, y_max) 设置 XY 属性域。
    sr.setDomain(xmin, xmax, ymin, ymax)

    # Create a dataset in target file geodataset to store all feature classes under dataset.
    arcpy.CreateFeatureDataset_management(os.path.join(outws, fgdb_name), "dataset", spatial_reference = sr)

    # A dictionary with keys of feature classes, and values of lists of absolute path of feature classes.
    direct_fcs = {}
    for g in gdbs:
        # Reset the working space to file geodatabase, which maybe changed to last dataset in last loop.
        arcpy.env.workspace = os.path.join(inws, g) 

        fcs = arcpy.ListFeatureClasses()
        if fcs is not None:
            for fc in fcs:
                try:
                    direct_fcs[fc].append(os.path.join(inws, g, fc))
                except:
                    direct_fcs[fc] = [os.path.join(inws, g, fc)]      
        else:
            print(arcpy.env.workspace, "Number of feature classes: 0")

    # Merge all feature classes with the same feature class names (in the same keys).
    for k in direct_fcs:
        arcpy.Merge_management(direct_fcs[k], os.path.join(outws, fgdb_name, "dataset", k))
