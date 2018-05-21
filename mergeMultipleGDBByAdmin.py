# -*- coding: utf-8 -*-
# test env: python 3.6, arcpro 2.1
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
                
def getDomainUnion(inws, gdbs):
    """
    Get the union of all the sr.domain of all FeatureClasses and Datasets directly in every gdbs.
    
    Arg: a list of gdbs.
    Return: a tuple of (xmin, ymin, xmax, ymax)
    """
    li_domain = []
    for g in gdbs:
        arcpy.env.workspace = os.path.join(inws, g)
        dss = arcpy.ListDatasets()
        fcs = arcpy.ListFeatureClasses()
        # Get the domain of FeatureClasses first.
        for fc in fcs:
            desc = arcpy.Describe(fc)
            sr = desc.spatialReference
            # Notice that sr.domain get a string of (xmin, ymin, xmax, ymax) separated by a space.
            li_domain.append([float(x) for x in sr.domain.split(" ")])
        # Get the domain of Datasets here.  
        for ds in dss:
            desc = arcpy.Describe(ds)
            sr = desc.spatialReference
            # Notice that sr.domain get a string of (xmin, ymin, xmax, ymax) separated by a space.
            li_domain.append([float(x) for x in sr.domain.split(" ")])
            
    df = pd.DataFrame(li_domain)
    return (df.iloc[:, 0].min(), df.iloc[:, 1].min(), df.iloc[:, 2].max(), df.iloc[:, 3].max())

if __name__ == '__main__':
    # Set input and output directories here
    inws = r'E:\DLG\gdb'
    outws = r'E:\DLG\gdb_by_admin'
    pattern_gdb = re.compile(".gdb$")

    # store all gdb files' absolut path, which has a dataset level.
    gdbs = [] 
    for g in locate_dir(pattern_gdb, root=inws):
        gdbs.append(g)
    
    # 读入图幅号与各区对应表格，图幅号表头“tfh”，区县表头"qy".
    df_gdbs = pd.read_excel(r"E:\DLG\rs1.xls")
    s_admin = set(df_gdbs["qy"]) # store unique value of administration area
    li_admin = list(s_admin)    
    d_admin = {li_admin.index(a): a for a in li_admin} # generate a dictionary to be convenient for choosing from.
    admin = input("""输入相应的数字，选择要合并GDB的区县!
    {0}""".format(d_admin))
    print("Your Choice: {0}.".format(d_admin[int(admin)]))

    df_admin = df_gdbs[df_gdbs['qy'] == d_admin[int(admin)]]
    li_tfh = list(df_admin['tfh'])

    # Define output FGDB name
    fgdb_name = "mergeByAdmin.gdb"
    # Create a new FGDB
    # Make sure this file geodatabase dosn't exist before running this script.
    arcpy.CreateFileGDB_management(outws, fgdb_name)

    gdbs_admin = []
    for g in gdbs:
        if g.split("\\")[-1][:-4] in li_tfh:
            gdbs_admin.append(g)

    xmin, ymin, xmax, ymax = getDomainUnion(inws, gdbs_admin)

    g = gdbs_admin[0]
    arcpy.env.workspace = os.path.join(inws, g)
    dss = arcpy.ListDatasets()
    fcs = arcpy.ListFeatureClasses()
    if fcs is not None:
        fc = fcs[0]
        desc = arcpy.Describe(fc)
        sr = desc.spatialReference
    elif dss is not None:
        ds = dss[0]
        desc = arcpy.Describe(ds)
        sr = desc.spatialReference
        
    # http://pro.arcgis.com/zh-cn/pro-app/arcpy/classes/spatialreference.htm
    # update the domain of x and y to the union of all feature classes from every gdbs.
    # Notice that when we set the domain of spatialReference, the sequence is: xmin, xmax, ymin, ymax, which is different
    # from the sequence what we get from sr.domain. setDomain (x_min, x_max, y_min, y_max) 设置 XY 属性域。
    sr.setDomain(xmin, xmax, ymin, ymax)
    # Create datasets with the name of dataset in target file geodataset with the same spatial reference as from the input geodatabases.
    arcpy.CreateFeatureDataset_management(os.path.join(outws, fgdb_name), "dataset", spatial_reference = sr)
    # Create datasets with the name of ds in target file geodataset for those FeatureClasses without dataset previously.
    arcpy.CreateFeatureDataset_management(os.path.join(outws, fgdb_name), "ds", spatial_reference = sr)

    # A dictionary with keys of feature classes, and values of lists of absolute path of feature classes directly in gdbs.
    direct_fcs = {}
    for g in gdbs_admin:
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
            print(arcpy.env.workspace, "Number of FeatureClasses: 0")

    # A dictionary with keys of feature classes, and values of lists of absolute path of feature classes in some datasets.
    indirect_fcs = {}
    for g in gdbs_admin:
        # Reset the working space to file geodatabase, which maybe changed to last dataset in last loop.
        arcpy.env.workspace = os.path.join(inws, g) 
        dss = arcpy.ListDatasets()
        if dss is not None:
            for ds in dss: 
                # Set workspace to the dataset in each input file geodatabase
                arcpy.env.workspace = os.path.join(inws, g, ds) 
                fcs = arcpy.ListFeatureClasses()
                if fcs is not None:
                    for fc in fcs:
                        try:
                            indirect_fcs[fc].append(os.path.join(inws, g, ds, fc))
                        except:
                            indirect_fcs[fc] = [os.path.join(inws, g, ds, fc)]            
                else:
                    print(arcpy.env.workspace, "Number of FeatureClasses: 0")
    
    # Merge input FeatureClasses to output FeatureClasses.
    for k in direct_fcs:
        arcpy.Merge_management(direct_fcs[k], os.path.join(outws, fgdb_name, "ds", k))
    for k in indirect_fcs:
        arcpy.Merge_management(indirect_fcs[k], os.path.join(outws, fgdb_name, dss[0], k))



