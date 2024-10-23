'''
The purpose of this script is to:
take the ID numbers of LiDAR index boxes
convert them to a text file,
Locate those filenames in a given directory
copy them to a new directory for easy import

Directions:
- make sure your lidar index file has the raster filenames within them
- make sure you know which raster extension you have
- select all index boxes in arc that you need
- export the selected index features as a .csv file into wherever you want
- follow the import directions when they come up
'''

import os, pandas, shutil

def findFiles():
    fpath = input(r"Path to folder*** contianing topo files you are looking for: ")
    tileName = input(r"Give path to .csv*** file containing tile IDs: ") # should be a .csv
    destination = input(r"Where do you want the files to be copied to: ")
    colName = input(r"Give name of column containing tile filenames: ") # should be a string name
    exName = input(r"Give the extension of the files you are looking for (ex '.tif' '.png': ")

    print(fpath, tileName) # check path names
    fileList = [f for f in os.listdir(fpath)]

    ### Get tile numbers
    open(tileName) # open file w/ tile names
    df = pandas.read_csv(tileName, sep=',', usecols=[str(colName)])
    colDataTemp = df[colName].values.tolist() # convert data frame to list
    colData = [str(f)+str(exName) for f in colDataTemp] # convert long int to str for finding files and add .tif extension
    print(colData)

    ### Copy tiles to new directory
    for x in fileList:
        if x in colData:
            print(fpath + r"\\" + x, destination)
            shutil.copy(fpath + r"\\" + x, destination) # copy files from input filepath to input destination
    return 1
findFiles()