# mergeMultipleGDB
Mainly used to merge multiple DLG geodatabase.
All of them have the same datasets (names, spatial reference with same GCS but different domains, etc.) and the same feature classes therein.

Search through a directory for file geodatabase files(*.gdb), get the union of domains and use it to define a new domain, merge all file geodatabases to a new file geodatabase(*.gdb).
The new file geodatabase will contain all datasets and feature classes from those separate file geodatabases.

mergeMultipleGDB_NoDataset.py assuming these file geodatabases have no feature classes in any datasets, but only directly in gdbs.
mergeMultipleGDB.py assuming these file geodatabases have no FCs directly in them, this only merge those FCs in some datasets.
mergeMultipleGDBByAdmin.py combine those two different situations, also give an option to choose which administration area to merge.

# Requirements
Tested in Python 3.6, arcpy from ArcPro

# Usage
Change the directory of gdb files in inws, the directory for new gdb file in outws.

