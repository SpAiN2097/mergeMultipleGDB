# mergeMultipleGDB
Mainly used to merge multiple DLG geodatabase, assuming these file geodatabases have no feature classes directly in them.
All of them have the same datasets (names, spatial reference with same GCS but different domains, etc.) and the same feature classes therein.

Search through a directory for file geodatabase files(*.gdb), get the union of domains and use it to define a new domain, merge all file geodatabases to a new file geodatabase(*.gdb).
The new file geodatabase will contain all datasets and feature classes from those separate file geodatabases.

# Requirements
Python 2.7.14, arcpy from ArcMap 10.6
Python 3.6, arcpy from ArcPro

# Usage
Change the directory of gdb files in inws, the directory for new gdb file in outws.

