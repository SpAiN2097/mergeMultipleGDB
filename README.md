# mergeMultipleGDB
Mainly used to mosaic multiple DLG geodatabase, assuming the feature classes in different gdb but have same names.
Search through a directory for file geodatabase files(*.gdb), merge all file geodatabases to a new file geodatabase(*.gdb).
The new file geodatabase will contain all datasets and feature classes from those separate file geodatabases.

# Requirements
Python 2.7.14, arcpy from ArcMap 10.6
Python 3.6, arcpy from ArcPro

# Usage
Change the directory of gdb files in inws, the directory for new gdb file in outws.

