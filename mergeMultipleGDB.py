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

    '''
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for d in dirs:
            if re.search(pattern, d):
                yield os.path.join(path, d)

def getDSDomainUnion(gdb_dss):
    """
    Get the union of all the sr.domain of all datasets in every gdb_dss.
    
    Arg: a list of gdbs.
    Return: a tuple of (xmin, ymin, xmax, ymax)
    
    """
    li_domain = []
    for g in gdb_dss:
        arcpy.env.workspace = os.path.join(inws, g)
        dss = arcpy.ListDatasets()
        for ds in dss:
            desc = arcpy.Describe(ds)
            sr = desc.spatialReference
            # Notice that sr.domain is a string of (xmin, ymin, xmax, ymax) separated by space.
            li_domain.append([float(x) for x in sr.domain.split(" ")])

    df = pd.DataFrame(li_domain)
    # Return min of xmin, ymin and max of xmax, ymax
    return (df.iloc[:, 0].min(), df.iloc[:, 1].min(), df.iloc[:, 2].max(), df.iloc[:, 3].max()) 


if __name__ == '__main__':
    # Set input and output directories here
    inws = r'E:\DLG\gdb_ds' # directory for gdbs with datasets in them, but no feature class directly in them.
    outws = r'E:\DLG\gdb_merge'
    pattern_gdb = re.compile(".gdb$")
    gdb_dss = [] # store all gdb files' absolut path.
    for g in locate_dir(pattern_gdb, root=inws):
        gdb_dss.append(g)

    # Define output FGDB name
    fgdb_name = "merged.gdb"

    # Create a new FGDB, make sure this file geodatabase dosen't exist when running this script.
    arcpy.CreateFileGDB_management(outws, fgdb_name)

    xmin, ymin, xmax, ymax = getDSDomainUnion(gdb_dss)

    g = gdb_dss[0]
    arcpy.env.workspace = os.path.join(inws, g)
    dss = arcpy.ListDatasets()
    for ds in dss:
        desc = arcpy.Describe(ds)
        sr = desc.spatialReference
        
        # http://pro.arcgis.com/zh-cn/pro-app/arcpy/classes/spatialreference.htm
        # update the domain of x and y to the union of all feature classes from every gdbs.
        # Notice that when we set the domain of spatialReference, the sequence is: xmin, xmax, ymin, ymax, which is different
        # from the sequence what we get from sr.domain. setDomain (x_min, x_max, y_min, y_max) 
        sr.setDomain(xmin, xmax, ymin, ymax)
        
        # Create datasets in target file geodataset with the same spatial reference and name as from the input geodatabases.
        arcpy.CreateFeatureDataset_management(os.path.join(outws, fgdb_name), ds, spatial_reference=sr)

    # A dictionary with keys of feature classes, and values of lists of absolute path of feature classes.
    indirect_fcs = {}
    # Assuming every gdb has the same datasets.
    for ds in dss:
        for g in gdb_dss:
            # set workspace to the dataset in each input file geodatabase
            arcpy.env.workspace = os.path.join(inws, g, ds) 
            fcs = arcpy.ListFeatureClasses()
            if fcs is not None:
                for fc in fcs:
                    try:
                        indirect_fcs[fc].append(os.path.join(inws, g, ds, fc))
                    except:
                        indirect_fcs[fc] = [os.path.join(inws, g, ds, fc)]            
            else:
                print(arcpy.env.workspace, "Number of feature classes: 0")

    # Merge all feature classes with the same feature class names (in the same keys).
    for k in indirect_fcs:
        arcpy.Merge_management(indirect_fcs[k], os.path.join(outws, fgdb_name, dss[0], k))
